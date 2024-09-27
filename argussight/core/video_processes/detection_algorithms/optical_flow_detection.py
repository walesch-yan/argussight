import cv2
import numpy as np

from argussight.core.video_processes.vprocess import Vprocess, FrameFormat
from typing import Tuple, Dict, Any
import yaml
import os
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from datetime import datetime
from multiprocessing import Queue
import queue
import subprocess
import uuid
import redis
import base64
import json


class OpticalFlowDetection(Vprocess):
    def __init__(
        self, shared_dict: DictProxy, lock: Lock, roi: Tuple[int, int, int, int]
    ) -> None:
        super().__init__(shared_dict, lock)
        self._roi = roi
        self._previous_frame = None
        self._processed_frame = None
        self._speeds = []
        self._current_speed = 0
        self._back_sub = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=10, detectShadows=True
        )

        self._frame_format = FrameFormat.CV2
        self._time_stamp_used = True
        self._command_timeout = 0.02

        self.load_params()
        self._currently_streaming = False
        self._stream_id = str(uuid.uuid1())
        self._redis_client = redis.StrictRedis(host="localhost", port=6379)

    @classmethod
    def create_commands_dict(cls) -> Dict[str, Any]:
        return {"change_roi": cls.change_roi}

    def load_params(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        params_file = os.path.join(
            current_dir, "../../configurations/optical_flow_detection.yaml"
        )
        with open(params_file, "r") as file:
            params = yaml.safe_load(file)

        self._flow_params = params["flow_params"]

    def get_stream_id(self) -> str:
        return self._stream_id

    def update_speed_value(self) -> None:
        if not self._speeds:
            self._current_speed = 0
        self._current_speed = sum(self._speeds) / len(self._speeds)
        self._speeds.clear()

    def get_background_percentage(self, frame):
        # Calculate the percentage of background in roi
        mask = self._back_sub.apply(frame)
        x, y, w, h = self._roi
        mask_roi = mask[y : y + h, x : x + w]
        non_background_pixels = np.count_nonzero(mask_roi)
        total_pixels = mask_roi.size
        background_percentage = 100 - (non_background_pixels / total_pixels * 100)

        return background_percentage, mask_roi

    def calculate_flow(self, frame, time_stamp: datetime):
        x, y, w, h = self._roi

        if self._previous_frame is None:
            self._previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self._last_speed_update = time_stamp
            self._last_time_stamp = time_stamp
            return self._previous_frame

        next_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Extract the ROI from the current and previous frame
        prvs_frame_roi = self._previous_frame[y : y + h, x : x + w]
        next_frame_roi = next_frame[y : y + h, x : x + w]

        # Update previous_frame for next iteration
        self._previous_frame = next_frame

        bg_percentage, bg_mask = self.get_background_percentage(frame)
        if 95 < bg_percentage:
            cv2.putText(
                frame,
                "Could not detect flow",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            return frame

        # Calculate optical flow within the ROI
        flow = cv2.calcOpticalFlowFarneback(
            prvs_frame_roi, next_frame_roi, None, **self._flow_params
        )
        # We do not want to consider the flow of the background
        binary_mask = binary_mask = (bg_mask > 0).astype(np.uint8)
        flow = flow * binary_mask[..., None]

        # Calculate and update speed
        flow_y = flow[..., 1]
        y_speed_per_second = (
            np.mean(np.abs(flow_y)[flow_y != 0])
            / (time_stamp - self._last_time_stamp).total_seconds()
        )
        self._last_time_stamp = time_stamp
        self._speeds.append(y_speed_per_second)

        if (time_stamp - self._last_speed_update).total_seconds() > 1:
            self.update_speed_value()
            self._last_speed_update = time_stamp

        # Visualize the optical flow within the ROI
        hsv_roi = np.zeros_like(frame[y : y + h, x : x + w])
        hsv_roi[..., 1] = 255
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        hsv_roi[..., 0] = ang * 180 / np.pi / 2
        hsv_roi[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        bgr_roi = cv2.cvtColor(hsv_roi, cv2.COLOR_HSV2BGR)

        # Overlay the ROI visualization and Speed-value on the original frame
        frame[y : y + h, x : x + w] = cv2.addWeighted(
            frame[y : y + h, x : x + w], 0.5, bgr_roi, 0.5, 0
        )
        cv2.putText(
            frame,
            f"Y Speed: {self._current_speed:.2f} pixels/second",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return frame

    def run(self, command_queue: Queue, response_queue: Queue) -> None:
        while True:
            try:
                order, args = command_queue.get(timeout=self._command_timeout)
                self.handle_command(order, response_queue, args)
            except queue.Empty:
                change = self.read_frame()
                if self._current_frame_number != 0:
                    self._processed_frame = (
                        self.calculate_flow(
                            self._current_frame, self._current_frame_time
                        )
                        if change
                        else self._processed_frame
                    )
                    if self._processed_frame is not None:
                        _, buffer = cv2.imencode(".jpg", self._processed_frame)
                        raw_image_data = buffer.tobytes()
                        frame_dict = {
                            "data": base64.b64encode(raw_image_data).decode("utf-8"),
                            "size": self._processed_frame.shape,
                        }
                        self._redis_client.publish(
                            "optical_flow", json.dumps(frame_dict)
                        )
                        if not self._currently_streaming:
                            self._video_stream_process = subprocess.Popen(
                                [
                                    "video-streamer",
                                    "-uri",
                                    "redis://localhost:6379",
                                    "-hs",
                                    "localhost",
                                    "-p",
                                    "9090",
                                    "-q",
                                    "4",
                                    "-s",
                                    str(self._processed_frame.shape)
                                    .replace("(", "")
                                    .replace(")", ""),
                                    "-of",
                                    "MPEG1",
                                    "-id",
                                    self._stream_id,
                                    "-irc",
                                    "optical_flow",
                                ],
                                close_fds=True,
                            )
                            self._currently_streaming = True

    def change_roi(self, roi: Tuple[int, int, int, int]):
        self._previous_frame = None
        self._processed_frame = None
        self._speeds.clear()
        self._roi = roi
