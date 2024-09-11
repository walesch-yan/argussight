from argussight.core.video_processes.vprocess import Vprocess, ProcessError
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from enum import Enum
from PIL import Image
from typing import Iterable, Dict, Any, Tuple
from multiprocessing import Queue
from datetime import datetime

import numpy as np
import queue
import cv2
import os


class SaveFormat(Enum):
    VIDEO = "video"
    FRAMES = "frames"
    BOTH = "both"


class VideoSaver(Vprocess):
    def __init__(
        self, shared_dict: DictProxy, lock: Lock, main_save_folder: str
    ) -> None:
        super().__init__(shared_dict, lock)
        self._main_save_folder = main_save_folder
        self._command_timeout = 0.04
        self._recording = (
            True  # change this value for stopping to save frames to iterable
        )

    def save_frame(self, frame: dict, folder_path: str):
        img = Image.frombytes("RGB", frame["size"], frame["frame"], "raw")
        img.save(
            os.path.join(folder_path, "img" + frame["time_stamp"] + ".jpg"),
            format="JPEG",
        )

    def is_within_main(self, target: str):
        abs_main = os.path.abspath(self._main_save_folder)
        abs_target = os.path.abspath(target)

        common_prefix = os.path.commonpath([abs_main])
        target_prefix = os.path.commonpath([abs_main, abs_target])

        return common_prefix == target_prefix

    def get_frame_from_element(
        self, element: Any
    ) -> Tuple[Tuple[int, int], bytes, str]:
        return element["size"], element["frame"], element["time_stamp"]

    def save_iterable_as_video(self, iterable: Iterable, save_folder: str) -> None:
        video_folder = os.path.join(save_folder, "videos")
        if not os.path.exists(video_folder):
            os.makedirs(video_folder, exist_ok=True)
        size_first, _, time_first = self.get_frame_from_element(iterable[0])
        _, _, time_last = self.get_frame_from_element(iterable[-1])
        output_file = os.path.join(video_folder, f"video_{time_first}-{time_last}.avi")

        out = cv2.VideoWriter(
            output_file, cv2.VideoWriter_fourcc(*"MJPG"), 30, size_first
        )

        for element in iterable:
            size, data, _ = self.get_frame_from_element(element)
            img = Image.frombytes("RGB", size, data, "raw")
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(open_cv_image)

        out.release()
        cv2.destroyAllWindows()

    def save_iterable(
        self, iterable: Iterable, save_format: str, personnal_folder: str
    ) -> None:
        save_folder = os.path.join(self._main_save_folder, personnal_folder)
        if not self.is_within_main(save_folder):
            raise ProcessError("Your path should not leave the main folder")
        if (
            save_format == SaveFormat.FRAMES.value
            or save_format == SaveFormat.BOTH.value
        ):
            _, _, time_first = self.get_frame_from_element(iterable[0])
            _, _, time_last = self.get_frame_from_element(iterable[-1])
            frames_folder = os.path.join(
                save_folder, f"frames_{time_first}-{time_last}"
            )
            if not os.path.exists(frames_folder):
                os.makedirs(frames_folder, exist_ok=True)

            for element in iterable:
                size, data, time = self.get_frame_from_element(element)
                frame = {"size": size, "frame": data, "time_stamp": time}
                self.save_frame(frame, frames_folder)

        if (
            save_format == SaveFormat.VIDEO.value
            or save_format == SaveFormat.BOTH.value
        ):
            self.save_iterable_as_video(iterable, save_folder)

    def add_to_iterable(self, frame: Dict) -> None:
        pass

    def run(self, command_queue: Queue, response_queue: Queue) -> None:
        while True:
            try:
                order, args = command_queue.get(timeout=self._command_timeout)
                self.handle_command(order, response_queue, args)
            except queue.Empty:
                if self._recording:
                    change = False
                    with self.lock:
                        current_frame_number = self.shared_dict["frame_number"]
                        if self._current_frame_number != current_frame_number:
                            current_frame = dict(self.shared_dict)
                            change = True
                    if change:
                        current_frame["time_stamp"] = datetime.strptime(
                            current_frame["time_stamp"], self._date_format
                        ).strftime(self._date_format)
                        self.add_to_iterable(current_frame)
