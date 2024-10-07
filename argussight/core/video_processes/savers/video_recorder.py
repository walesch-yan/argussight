from typing import Any, Dict, Tuple
import os
import glob
from PIL import Image
import shutil

from argussight.core.video_processes.savers.video_saver import VideoSaver
from argussight.core.video_processes.vprocess import ProcessError


def remove_start_end(main: str, start: str, end: str) -> str:
    if start in main:
        main = main.rsplit(start, 1)[1]
    if main.endswith(end):
        main = main[: -len(end)]
    return main


def delete_all_files(folder_path: str) -> None:
    if os.path.exists(folder_path):
        try:
            # Remove the entire directory tree
            shutil.rmtree(folder_path)
            print(f"Deleted {folder_path} and all its contents.")
        except Exception as e:
            print(f"Failed to delete {folder_path}: {e}")
    else:
        print(f"The folder {folder_path} does not exist.")


class Recorder(VideoSaver):
    def __init__(self, collector_config, exposed_parameters: Dict[str, Any]) -> None:
        super().__init__(collector_config, exposed_parameters)
        self._recording = False
        self._temp_counter = 0

        # Make sure that there are no files in the temp folder from old recording failures
        delete_all_files(self._parameters["temp_folder"])
        os.makedirs(self._parameters["temp_folder"])

        self._parameters["temp_folder"] = os.path.join(
            self._parameters["temp_folder"], f"{self._temp_counter}"
        )

    @classmethod
    def create_commands_dict(cls) -> Dict[str, Any]:
        result = super().create_commands_dict()
        result.update(
            {
                "start": cls.start_record,
                "stop": cls.stop_record,
            }
        )
        return result

    def add_to_iterable(self, frame: Dict) -> None:
        if not os.path.exists(self._parameters["temp_folder"]):
            os.makedirs(self._parameters["temp_folder"], exist_ok=True)
        self.save_frame(frame, self._parameters["temp_folder"])

    def get_frame_from_element(
        self, element: Any
    ) -> Tuple[Tuple[int, int], bytes, str]:
        frame = Image.open(element, "r")
        raw_data = frame.convert("RGB").tobytes()

        return frame.size, raw_data, remove_start_end(element, "img", ".jpg")

    def start_record(self) -> None:
        if self._recording:
            raise ProcessError("Already recording")
        self._recording = True

    def stop_record(self) -> None:
        if not self._recording:
            raise ProcessError("There is no recording to stop")

        image_names = [
            os.path.join(self._parameters["temp_folder"], os.path.basename(image))
            for image in glob.glob(
                os.path.join(self._parameters["temp_folder"], "*jpg")
            )
        ]

        # create a process to make a video from the recorded frames
        self.executor.submit(
            self._stop_record,
            image_names,
            self._parameters["temp_folder"],
        )

        # go to next recording folder
        self._parameters["temp_folder"] = self._parameters["temp_folder"].rsplit("/")[0]
        self._temp_counter += 1
        self._parameters["temp_folder"] = os.path.join(
            self._parameters["temp_folder"], f"{self._temp_counter}"
        )

        self._recording = False

    def _stop_record(self, images_names, temp_folder):
        self.save_iterable(images_names)
        delete_all_files(temp_folder)
