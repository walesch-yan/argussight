import cv2
import numpy as np
from argussight.core.video_processes.vprocess import Vprocess, FrameFormat
from typing import Tuple
import time
import yaml
import os
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock

class FlowDetection(Vprocess):
    def __init__(self, shared_dict: DictProxy, lock: Lock, roi: Tuple[int,int,int,int]) -> None:
        super().__init__(shared_dict, lock)
        self._roi = roi
        self._previous_frame = None
        self._p0 = None
        self._frame_format = FrameFormat.CV2 # this process needs a cv2 image format for computations

        self.load_params()
        
    def load_params(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        params_file = os.path.join(current_dir, 'flow_detection.yaml')
        with open(params_file, 'r') as file:
            params = yaml.safe_load(file)
        
        self._feature_params = params['feature_params']
        self._lk_params = params['lk_params']

        self._lk_params['criteria'] = tuple(self._lk_params['criteria'])

    def select_feature_points(self, roi_gray) -> np.ndarray:
        # Detect feature points in the ROI
        points = cv2.goodFeaturesToTrack(roi_gray, mask=None, **self._feature_params)
        
        if points is not None:
            # Adjust the points to the whole frame
            points[:, 0, 0] += self._roi[0]
            points[:, 0, 1] += self._roi[1]
        
        return points
    
    def is_point_in_roi(self, x: int, y:int) -> bool:
        rx, ry, rw, rh = self._roi
        return rx<=x<=rx+rw and ry<=y<=ry+rh
    
    def remove_outliers(self) -> None:
        if self._p0 is not None:
            result = [point for point in self._p0 if self.is_point_in_roi(*point[0])]
            self._p0 = np.array(result) if len(result)>0 else None
    
    def detect_and_track_features(self, frame) -> None:            
        x, y, w, h = self._roi
        
        if self._previous_frame is None:
            self._previous_frame = frame.copy()
            gray_previous_frame = cv2.cvtColor(self._previous_frame, cv2.COLOR_BGR2GRAY)
            roi_gray = gray_previous_frame[y:y+h, x:x+w]
            
            self._p0 = self.select_feature_points(roi_gray)
        else:
            gray_previous_frame = cv2.cvtColor(self._previous_frame, cv2.COLOR_BGR2GRAY)
        
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self._p0 is not None:
            # Calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(gray_previous_frame, gray_frame, self._p0, None, **self._lk_params)
            
            # Check if points were found
            if p1 is not None:
                # Select good points
                good_new = p1[st == 1]

                # Update the previous frame and previous points
                self._p0 = good_new.reshape(-1, 1, 2)
                self._previous_frame = frame.copy()
                
                # Draw the circles
                for i, new in enumerate(good_new):
                    a, b = new.ravel().astype(int)
                    frame = cv2.circle(frame, (a, b), 8, (0, 255, 0), 2)
            
            if len(self._p0)<= 5:
                # Select new points if old ones moved out of frame
                new_points = self.select_feature_points(gray_frame[y:y+h, x:x+w])
                
                if new_points is not None:
                    self._p0 = np.concatenate([self._p0, new_points], axis=0) if self._p0 is not None else new_points
        else:
            self._previous_frame = None
        
        # Draw ROI
        frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 2)

        self.remove_outliers()

        return frame
    
    def run(self):
        processed_frame = None
        while True:
            change = self.read_frame()
            if self._current_frame_number != 0:
                processed_frame = self.detect_and_track_features(self._current_frame) if change else processed_frame
                if processed_frame is not None:
                    cv2.imshow('Live Stream', processed_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            time.sleep(0.04)
        
        cv2.destroyAllWindows()
