from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock

class Vprocess:
    def __init__(self, shared_dict: DictProxy = None, lock: Lock = None) -> None:
        self.shared_dict = shared_dict
        self.lock = lock
        self._current_frame_number = 0
        self._current_frame = None
        self._missed_frames = 0
    
    def read_frame(self) -> bool:
        with self.lock:
            if self._current_frame_number != self.shared_dict["frame_number"]:
                self._current_frame = self.shared_dict["frame"].copy()
                self._missed_frames += self.shared_dict["frame_number"] - self._current_frame_number - 1
                self._current_frame_number = self.shared_dict["frame_number"]
                return True
        
        return False

    def run(self) -> None:
        pass

class Test(Vprocess):
    def __init__(self) -> None:
        super().__init__()
    
    def run(self) -> None:
        print("Test succeeded")