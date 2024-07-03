import cv2
import numpy as np
from argussight.core.video_processes.vprocess import Vprocess
from typing import Tuple
import time
from collections import deque

class FlowDetection(Vprocess):
    def __init__(self, roi: Tuple[int,int,int,int]):
        super().__init__()
        self._roi = roi

        self._previous_frame = None
        self._p0 = None

        self._feature_params = dict(maxCorners=5, qualityLevel=0.7, minDistance=50, blockSize=7)
        self._lk_params = dict(winSize=(15, 15), maxLevel=2,
                        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
    
    def detect_and_track_features(self, frame):
            
        x, y, w, h = self._roi
        
        if self._previous_frame is None:
            self._previous_frame = frame.copy()
            gray_previous_frame = cv2.cvtColor(self._previous_frame, cv2.COLOR_BGR2GRAY)
            roi_gray = gray_previous_frame[y:y+h, x:x+w]
            
            # Detect feature points in the ROI
            self._p0 = cv2.goodFeaturesToTrack(roi_gray, mask=None, **self._feature_params)
            
            if self._p0 is not None:
                # Adjust the points to the whole frame
                self._p0[:, 0, 0] += x
                self._p0[:, 0, 1] += y
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
                # Detect new feature points in the current frame
                gray_frame_roi = gray_frame[y:y+h, x:x+w]
                new_points = cv2.goodFeaturesToTrack(gray_frame_roi, mask=None, **self._feature_params)
                
                if new_points is not None:
                    # Adjust new points to the whole frame
                    new_points[:, 0, 0] += x
                    new_points[:, 0, 1] += y
                    
                    self._p0 = np.concatenate([self._p0, new_points], axis=0) if self._p0 is not None else new_points
        else:
            self._previous_frame = None
        
        frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (255,0,0), 2)

        return frame
    
    def run(self, queue: deque):
        while len(queue)>=1:
            frame = queue.popleft()
            processed_frame = self.detect_and_track_features(frame)
            cv2.imshow('Live Stream', processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.04)
        
        cv2.destroyAllWindows()
