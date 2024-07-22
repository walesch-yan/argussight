from multiprocessing import Queue
from datetime import datetime
from threading import Event
from argussight.core.video_processes.vprocess import ProcessError
import queue


class Manager():
    def __init__(self, command_queue: Queue, response_queue: Queue, finished_event: Event, failed_event: Event) -> None:
        self._commands_list = queue.Queue(maxsize=20) # commands that are waiting to be processed by Manager
        self._command_queue = command_queue # commands that are sent to process for being processed
        self._response_queue = response_queue
        self._finished_event = finished_event
        self._failed_event = failed_event

    def receive_command(self, command: str, wait_time: int, processed_event: Event, result_queue: queue.Queue, args) -> None:
        if self._commands_list.full():
            raise ProcessError(f"Cannot execute command {command}: too many commands in waiting list")
        self._commands_list.put({
            "command": command,
            "max_wait_time": wait_time,
            "time_stamp": datetime.now(),
            "args": args,
            "processed_event": processed_event,
            "result_queue": result_queue,
        })
    
    def handle_commands(self) -> None:
        while not self._commands_list.empty():
            command = self._commands_list.get()

            # Check if command is alive
            if (datetime.now() - command["time_stamp"]).total_seconds() > command["max_wait_time"]:
                continue

            self._command_queue.put((command["command"], command["args"]))
            command["processed_event"].set()

            try:
                result = self._response_queue.get(timeout=command["max_wait_time"])
                command["result_queue"].put(result)

            except queue.Empty:
                self._failed_event.set()
                break
        
        self._finished_event.set()