from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from argussight.core.video_processes.video_saver import VideoSaver
from collections import deque
from typing import Dict

class StreamBuffer(VideoSaver):
    def __init__(self, shared_dict: DictProxy, lock: Lock, max_queue_len: int, main_save_folder: str) -> None:
        super().__init__(shared_dict, lock, main_save_folder)
        self._commands = {
            "save": self.save_queue
        }
        self._queue = deque(maxlen=max_queue_len)

    def save_queue(self, save_format: str, personnal_folder: str) -> None:
        self.save_iterable(self._queue, save_format, personnal_folder)

    def add_to_iterable(self, frame: Dict) -> None:
        self._queue.append(frame)