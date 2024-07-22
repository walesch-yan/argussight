from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from argussight.core.video_processes.vprocess import Vprocess, ProcessError
from collections import deque
from enum import Enum
from PIL import Image
import os
import cv2
import numpy as np
from multiprocessing import Queue
import queue
from datetime import datetime

class SaveFormat(Enum):
    VIDEO = 'video'
    FRAMES = 'frames'
    BOTH = 'both'

class VideoSaver(Vprocess):
    def __init__(self, shared_dict: DictProxy, lock: Lock, max_queue_len, main_save_folder: str) -> None:
        super().__init__(shared_dict, lock)
        self._commands = {
            "save": self.save_queue
        }
        self._command_timeout = 0.04
        self._queue = deque(maxlen=max_queue_len)
        self._main_save_folder = main_save_folder

    def save_frame(self, frame: dict, folder_path: str):
        img = Image.frombytes("RGB", frame['size'], frame['frame'], "raw")
        img.save(os.path.join(folder_path, 'img'+ frame['time_stamp'] + '.jpg'), format='JPEG')

    def save_queue_as_video(self, save_folder) -> None:
        video_folder = os.path.join(save_folder, 'videos')
        if not os.path.exists(video_folder):
            os.makedirs(video_folder, exist_ok=True)
        output_file = os.path.join(video_folder, f"video_{self._queue[0]['time_stamp']}-{self._queue[-1]['time_stamp']}.avi")

        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'MJPG') , 30, self._queue[0]['size'])

        for frame in self._queue:
            img = Image.frombytes("RGB", frame['size'], frame['frame'], "raw")
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(open_cv_image)
        
        out.release()
        cv2.destroyAllWindows()
    
    def is_within_main(self, target):
        abs_main = os.path.abspath(self._main_save_folder)
        abs_target = os.path.abspath(target)
        
        common_prefix = os.path.commonpath([abs_main])
        target_prefix = os.path.commonpath([abs_main, abs_target])
        
        return common_prefix == target_prefix

    def save_queue(self, save_format: str, personnal_folder: str) -> None:
        save_folder = os.path.join(self._main_save_folder, personnal_folder)
        if not self.is_within_main(save_folder):
            raise ProcessError("Your path should not leave the main folder")
        print(f"saving video at {save_folder}")
        if save_format == SaveFormat.FRAMES.value or save_format == SaveFormat.BOTH.value:
            frames_folder = os.path.join(save_folder, f"frames_{self._queue[0]['time_stamp']}-{self._queue[-1]['time_stamp']}")
            if not os.path.exists(frames_folder):
                os.makedirs(frames_folder, exist_ok=True)

            for frame in self._queue:
                self.save_frame(frame, frames_folder)
        
        if save_format == SaveFormat.VIDEO.value or save_format == SaveFormat.BOTH.value:
            self.save_queue_as_video(save_folder)

    def run(self, command_queue: Queue, response_queue: Queue) -> None:
        while True:
            try:
                order, args = command_queue.get(timeout=self._command_timeout)
                self.handle_command(order, response_queue, args)
            except queue.Empty:
                change = False
                with self.lock:
                    current_frame_number = self.shared_dict["frame_number"]
                    if self._current_frame_number != current_frame_number:
                        current_frame = dict(self.shared_dict)
                        change = True
                if change:
                    current_frame["time_stamp"] = datetime.strptime(current_frame["time_stamp"], self._date_format).strftime(self._date_format)
                    self._queue.append(current_frame)