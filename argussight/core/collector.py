import redis
import os
from argussight.core.config import CollectorConfiguration, SaveFormat
from PIL import Image
import json
import base64
from collections import deque
import cv2
import numpy as np
from multiprocessing.connection import Connection

class Collector:
    def __init__(self, config: CollectorConfiguration, pipe_connection: Connection):
        self._client = redis.StrictRedis(host=config.redis.host, port=config.redis.port)
        self._channel = config.redis.channel
        self._max_queue_length = config.queue.max_length
        self._queue = deque(maxlen=self._max_queue_length)
        self.pipe = pipe_connection
        self._save_folder = config.queue.save_folder
        self._save_format = config.queue.save_format

        if not os.path.exists(self._save_folder):
            os.makedirs(self._save_folder, exist_ok=True)

    def save_frame(self, frame: dict, folder_path: str):
        data = base64.b64decode(frame['data'])
        img = Image.frombytes("RGB", frame['size'], data, "raw")
        img.save(os.path.join(folder_path, 'img'+ frame['time'] + '.jpg'), format='JPEG')

    def process_frame(self, frame: dict) -> None:
        self._queue.append(frame)
        self.pipe.send(frame)
    
    def save_queue_as_video(self) -> None:
        video_folder = os.path.join(self._save_folder, 'videos')
        if not os.path.exists(video_folder):
            os.makedirs(video_folder, exist_ok=True)
        output_file = os.path.join(video_folder, f"video_{self._queue[0]['time']}-{self._queue[-1]['time']}.avi")

        out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'MJPG') , 30, self._queue[0]['size'])

        for frame in self._queue:
            data = base64.b64decode(frame['data'])
            img = Image.frombytes("RGB", frame['size'], data, "raw")
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(open_cv_image)
        
        out.release()
        cv2.destroyAllWindows()

    def save_queue(self) -> None:
        if self._save_format == SaveFormat.FRAMES or self._save_format == SaveFormat.BOTH:
            frames_folder = os.path.join(self._save_folder, f"frames_{self._queue[0]['time']}-{self._queue[-1]['time']}")
            if not os.path.exists(frames_folder):
                os.makedirs(frames_folder, exist_ok=True)

            for frame in self._queue:
                self.save_frame(frame, frames_folder)
        
        if self._save_format == SaveFormat.VIDEO or self._save_format == SaveFormat.BOTH:
            self.save_queue_as_video()

    def start(self) -> None:
        pubsub = self._client.pubsub()
        pubsub.subscribe(self._channel)

        for message in pubsub.listen():
            if message["type"] == "message":

                if message["data"] == b'save queue':
                    self.save_queue()
                    continue

                frame = json.loads(message["data"])
                self.process_frame(frame)