from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from enum import Enum
from PIL import Image
from typing import Tuple, Dict, Any
import cv2
import numpy as np
from datetime import datetime
from multiprocessing import Queue
import queue
import time

class ProcessError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class FrameFormat(Enum):
    CV2= 'cv2'
    PIL= 'pil'
    RAW= 'raw'

class Vprocess:
    def __init__(self, shared_dict: DictProxy = None, lock: Lock = None) -> None:
        self.shared_dict = shared_dict
        self.lock = lock
        self._current_frame_number = -1
        self._current_frame = None
        self._missed_frames = 0

        # Please change the following three variables (if you need to) in your subclasses (not here!)
        self._frame_format: FrameFormat = FrameFormat.RAW # Format your frames should convert to
        self._time_stamp_used = False # If you need self._current_frame_time, set this to true
        self._commands = self.create_commands_dict() # Dictionary of all commands that can be executed via command_queue
        self._command_timeout = 1 # Time the process waits for new commands to arrive in seconds
        self._date_format = "%H:%M:%S.%f"

    @classmethod
    def create_commands_dict(cls) -> Dict[str, Any]:
        return {}
        
    def read_frame(self) -> bool:
        with self.lock:
            current_frame_number = self.shared_dict["frame_number"]
            if self._current_frame_number != current_frame_number:
                if self._time_stamp_used:
                    self._current_frame_time = datetime.strptime(self.shared_dict['time_stamp'], self._date_format)

                self.copy_frame(self.shared_dict["frame"], self.shared_dict["size"])
                if self._current_frame_number != -1:
                    self._missed_frames += current_frame_number - self._current_frame_number - 1
                    if current_frame_number > self._current_frame_number + 1:
                        print(f"Frames Missed in Total: {self._missed_frames}")
                else:
                    print(f"Started reading at frame {current_frame_number}")
                self._current_frame_number = current_frame_number
                return True
        
        return False
    
    def copy_frame(self, frame_data: bytes, frame_size: Tuple[int, int, int]) -> None:
        match self._frame_format:
            case FrameFormat.RAW:
                self._current_frame = frame_data
            case FrameFormat.PIL:
                self._current_frame = Image.frombytes("RGB", frame_size, frame_data, "raw")
            case FrameFormat.CV2:
                img = Image.frombytes("RGB", frame_size, frame_data, "raw")
                self._current_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            case _:
                raise TypeError(f"FrameFormat has no type: {self._frame_format}")

    def run(self, command_queue: Queue, response_queue: Queue) -> None:
        while True:
            try:
                order, args = command_queue.get(timeout=self._command_timeout)
                self.handle_command(order, response_queue, args)
            except queue.Empty:
                continue

    def handle_command(self, order: str, response_queue: Queue, args) -> None:
        if order not in self._commands:
            response_queue.put(ProcessError(f"Order {order} is not known for process of type {type(self)}."))
            return
        
        try:
            self._commands[order](self, *args)
            response_queue.put("Order {order} succeeded")
        except Exception as e:
            response_queue.put(e)

class Test(Vprocess):
    def __init__(self, shared_dict: DictProxy = None, lock: Lock = None) -> None:
        super().__init__(shared_dict, lock)
        self._commands["print"] = self.print
    
    def run(self, command_queue: Queue, response_queue: Queue) -> None:
        print("Running test process")
        super().run(command_queue, response_queue)

    def print(self, text:str ):
        print(text)
        time.sleep(2)