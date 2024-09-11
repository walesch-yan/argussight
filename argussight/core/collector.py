import redis
from argussight.core.config import CollectorConfiguration
import json
import base64
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock


class Collector:
    def __init__(
        self, config: CollectorConfiguration, shared_dict: DictProxy, lock: Lock
    ):
        self._client = redis.StrictRedis(host=config.redis.host, port=config.redis.port)
        self._channel = config.redis.channel
        self.shared_dict = shared_dict
        self.lock = lock

    def process_frame(self, frame: dict) -> None:
        # decode the received frame data before saving
        frame["data"] = base64.b64decode(frame["data"])
        with self.lock:
            self.shared_dict["frame"] = frame["data"]
            self.shared_dict["frame_number"] += 1
            self.shared_dict["time_stamp"] = frame["time"]
            self.shared_dict["size"] = frame["size"]

    def start(self) -> None:
        pubsub = self._client.pubsub()
        pubsub.subscribe(self._channel)

        for message in pubsub.listen():
            if message["type"] == "message":

                frame = json.loads(message["data"])
                self.process_frame(frame)
