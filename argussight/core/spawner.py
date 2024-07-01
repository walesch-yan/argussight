import yaml
import multiprocessing
import time
from typing import List
import importlib
from collections import deque

from argussight.core.video_processes.vprocess import Vprocess, Test

class Spawner:
    def __init__(self, pipe_connection: multiprocessing.connection.Connection, queue_maxlen: int = 200) -> None:
        self.config_file = 'argussight/core/video_processes/config.yaml'
        self.processes = {}
        self.worker_classes = {}
        self.pipe = pipe_connection
        self.queue = deque(maxlen=queue_maxlen)

    def load_config(self) -> None:
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        self.load_worker_classes()

    def load_worker_classes(self):
        worker_classes_config = self.config['worker_classes']
        modules_path = self.config['modules_path']
        for key, class_path in worker_classes_config.items():
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(modules_path + '.' + module_name)
            self.worker_classes[key] = getattr(module, class_name)
        
    def create_worker(self, worker_type: str, *args) -> Vprocess:
        if worker_type not in self.worker_classes.keys():
            raise ValueError(f"Unknown worker type: {worker_type}")
        return self.worker_classes.get(worker_type)(*args)

    def start_processes(self) -> None:
        for process_config in self.config["processes"]:
            worker_type = process_config["type"]
            name = process_config["name"]
            args = process_config.get("args", [])
            worker_instance = self.create_worker(worker_type, *args)
            p = multiprocessing.Process(target=worker_instance.run)
            p.start()
            self.processes[name] = p

    def terminate_processes(self, names: List[str]) -> None:
        for name in names:
            self.processes[name].terminate()
            self.processes[name].join()
            del self.processes[name]

    def manage_processes(self) -> None:
        try:
            while True:
                while self.pipe.poll():
                    frame = self.pipe.recv()
                    self.queue.append(frame)
                time.sleep(0.04)
        except KeyboardInterrupt:
            self.terminate_processes(list(self.processes.keys()))

    def run(self):
        self.load_config()
        self.start_processes()
        self.manage_processes()