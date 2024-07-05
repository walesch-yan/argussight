import yaml
import multiprocessing
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
import time
from typing import List
import importlib
import os

from argussight.core.video_processes.vprocess import Vprocess

class Spawner:
    def __init__(self, shared_dict: DictProxy, lock: Lock) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._config_file = os.path.join(current_dir, 'video_processes/config.yaml')
        self._processes = {}
        self._worker_classes = {}
        self.shared_dict = shared_dict
        self.lock = lock

    def load_config(self) -> None:
        with open(self._config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        self.load_worker_classes()

    def load_worker_classes(self):
        worker_classes_config = self.config['worker_classes']
        modules_path = self.config['modules_path']
        for key, class_path in worker_classes_config.items():
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(modules_path + '.' + module_name)
            self._worker_classes[key] = getattr(module, class_name)
        
    def create_worker(self, worker_type: str, *args) -> Vprocess:
        if worker_type not in self._worker_classes.keys():
            raise ValueError(f"Unknown worker type: {worker_type}")
        return self._worker_classes.get(worker_type)(self.shared_dict, self.lock, *args)

    def start_processes(self) -> None:
        for process_config in self.config["processes"]:
            worker_type = process_config["type"]
            name = process_config["name"]
            args = process_config.get("args", [])
            worker_instance = self.create_worker(worker_type, *args)
            p = multiprocessing.Process(target=worker_instance.run)
            p.start()
            self._processes[name] = p

    def terminate_processes(self, names: List[str]) -> None:
        for name in names:
            self._processes[name].terminate()
            self._processes[name].join()
            del self._processes[name]

    def manage_processes(self) -> None:
        try:
            while True:
                time.sleep(0.04)
        except KeyboardInterrupt:
            self.terminate_processes(list(self._processes.keys()))

    def run(self):
        self.load_config()
        self.start_processes()
        self.manage_processes()