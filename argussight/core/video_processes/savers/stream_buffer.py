from collections import deque
from typing import Dict, Any

from argussight.core.video_processes.savers.video_saver import VideoSaver


class StreamBuffer(VideoSaver):
    def __init__(
        self,
        collector_config,
    ) -> None:
        super().__init__(collector_config)
        self._queue = deque(maxlen=self._parameters["max_queue_len"])

    @classmethod
    def create_commands_dict(cls) -> Dict[str, Any]:
        return {"save": cls.save_queue}

<<<<<<< HEAD
    def save_queue(self, save_format: str, personnal_folder: str) -> None:
        queue = self._queue.copy()
        self.executor.submit(self.save_iterable, queue, save_format, personnal_folder)
=======
    def save_queue(self) -> None:
        self.save_iterable(
            self._queue,
            self._parameters["save_format"],
            self._parameters["personnal_folder"],
        )
>>>>>>> 0bc6265 (usage of configuration files for processes)

    def add_to_iterable(self, frame: Dict) -> None:
        self._queue.append(frame)
