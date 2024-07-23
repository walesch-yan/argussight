from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
from typing import Any, Dict, Tuple
from argussight.core.video_processes.video_saver import VideoSaver
from argussight.core.video_processes.vprocess import ProcessError
import os
import glob
from PIL import Image

def remove_start_end(main: str, start: str, end: str) -> str:
    if main.startswith(start):
        main = main[len(start):]
    if main.endswith(end):
        main = main[:-len(end)]
    return main

def delete_all_files(folder_path: str) -> None:
    files = glob.glob(os.path.join(folder_path, '*'))
    
    for file in files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Failed to delete {file}: {e}")

class Recorder(VideoSaver):
    def __init__(self, shared_dict: DictProxy, lock: Lock, main_save_folder: str, temp_folder: str) -> None:
        super().__init__(shared_dict, lock, main_save_folder)
        self._commands = {
            "start": self.start_record,
            "stop": self.stop_record
        }
        self._recording = False
        self._temp_folder = temp_folder

        # Make sure that there are no files in the temp folder from old recording failures
        delete_all_files(self._temp_folder)

    def add_to_iterable(self, frame: Dict) -> None:
        if not os.path.exists(self._temp_folder):
            os.makedirs(self._temp_folder, exist_ok=True)
        self.save_frame(frame, self._temp_folder)
    
    def get_frame_from_element(self, element: Any) -> Tuple[Tuple[int, int], bytes, str]:
        img_fpath = os.path.join(self._temp_folder, element)
        frame = Image.open(img_fpath, "r")
        raw_data = frame.convert("RGB").tobytes()

        return frame.size, raw_data, remove_start_end(element, "img", ".jpg")

    def start_record(self) -> None:
        if self._recording:
            raise ProcessError("Already recording")
        self._recording = True
    
    def stop_record(self, save_format, personnal_folder) -> None:
        if not self._recording:
            raise ProcessError("There is no recording to stop")
        
        image_names = [os.path.basename(image) for image in glob.glob(os.path.join(self._temp_folder, '*jpg'))]
        print(image_names)
        self.save_iterable(image_names, save_format, personnal_folder)

        delete_all_files(self._temp_folder)
        self._recording = False