import yaml
import multiprocessing
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
import time
from typing import List, Dict, Any, Union
import importlib
import os
import Levenshtein

from argussight.core.video_processes.vprocess import Vprocess

class ProcessError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

def find_close_key(d: dict, key: str, max_distance: int = 3) -> Union[str, None]:
    min_distance = float('inf')
    closest_key = None
    
    for dict_key in d:
        distance = Levenshtein.distance(key, dict_key)
        if distance < min_distance:
            min_distance = distance
            closest_key = dict_key
    
    if min_distance<=max_distance:
        return closest_key
    
    return None

class Spawner:
    def __init__(self, shared_dict: DictProxy, lock: Lock) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._config_file = os.path.join(current_dir, 'video_processes/config.yaml')
        self._processes = {}
        self._worker_classes = {}
        self.shared_dict = shared_dict
        self.lock = lock
        
        self.load_config()

    def load_config(self) -> None:
        with open(self._config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        self.load_worker_classes()
        self.start_processes(self.config["processes"])

    def load_worker_classes(self):
        worker_classes_config = self.config['worker_classes']
        modules_path = self.config['modules_path']
        for key, class_path in worker_classes_config.items():
            module_name, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(modules_path + '.' + module_name)
            self._worker_classes[key] = getattr(module, class_name)
        
    def create_worker(self, worker_type: str, *args) -> Vprocess:
        return self._worker_classes.get(worker_type)(self.shared_dict, self.lock, *args)

    def start_processes(self, processes: List[Dict[str, Any]]) -> None:
        # First check for uniqueness of name and existance of type
        for process in processes:
            worker_type = process["type"]
            name = process["name"]
            if name in self._processes:
                raise ProcessError(f"Process names must be unique. '{name}' already exists. Either terminate '{name}' or choose a different unique name")
            if worker_type not in self._worker_classes:
                raise ProcessError(f"Type {worker_type} does not exist")
            
        for process in processes:
            worker_type = process["type"]
            name = process["name"]
            args = process["args"] if process['args'] else []
            worker_instance = self.create_worker(worker_type, *args)
            p = multiprocessing.Process(target=worker_instance.run)
            p.start()
            print(f"started {name} of type {worker_type}")
            self._processes[name] = p

    def terminate_processes(self, names: List[str]) -> None:
        for name in names:
            if name not in self._processes:
                errorMessage = f"{name} is not a running process."
                closest_key = find_close_key(self._processes, name)
                if closest_key:
                    errorMessage += f" Did you mean: {closest_key}"

                raise ProcessError(errorMessage)
        for name in names:
            self._processes[name].terminate()
            self._processes[name].join()
            del self._processes[name]
            print(f"terminated {name}")

    def manage_processes(self) -> None:
        try:
            while True:
                time.sleep(0.04)
        except KeyboardInterrupt:
            self.terminate_processes(list(self._processes.keys()))