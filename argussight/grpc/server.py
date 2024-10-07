import grpc
from concurrent import futures
import time
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
import json

from argussight.core.spawner import Spawner, ProcessError


class SpawnerService(pb2_grpc.SpawnerServiceServicer):
    def __init__(self, collector_config):
        self.spawner = Spawner(collector_config)
        self._min_waiting_time = 1

    def StartProcesses(self, request, context):
        try:
            self.spawner.start_process(request.name, request.type)
            stream_id = self.spawner.get_stream_id(request.name)
            return pb2.StartProcessesResponse(status="success", stream_id=stream_id)
        except ProcessError as e:
            return pb2.StartProcessesResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.StartProcessesResponse(
                status="failure", error_message=f"Unexpected error: {str(e)}"
            )

    def TerminateProcesses(self, request, context):
        try:
            self.spawner.terminate_processes(request.names)
            return pb2.TerminateProcessesResponse(status="success")
        except ProcessError as e:
            return pb2.TerminateProcessesResponse(
                status="failure", error_message=str(e)
            )
        except Exception as e:
            return pb2.TerminateProcessesResponse(
                status="failure", error_message=f"Unexpected error: {str(e)}"
            )

    def ManageProcesses(self, request, context):
        try:
            if request.wait_time < self._min_waiting_time:
                return pb2.ManageProcessesResponse(
                    status="failure",
                    error_message=f"Please choose wait_time to be larger than {self._min_waiting_time}",
                )
            self.spawner.manage_process(
                request.name,
                request.order,
                request.wait_time,
                [json.loads(arg) for arg in request.args],
            )
            return pb2.ManageProcessesResponse(status="success")
        except ProcessError as e:
            return pb2.ManageProcessesResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.ManageProcessesResponse(
                status="failure", error_message=f"Unexpected error: {str(e)}"
            )

    def GetProcesses(self, request, context):
        try:
            running_processes, available_types = self.spawner.get_processes()
            running_dict = {}
            for name, process in running_processes.items():
                current_commands = []
                for key, args in process["commands"].items():
                    current_commands.append(pb2.Command(command=key, args=args))
                running_dict[name] = pb2.RunningProcessDictionary(
                    type=process["type"],
                    commands=current_commands,
                )
            return pb2.GetProcessesResponse(
                status="success",
                running_processes=running_dict,
                available_process_types=available_types,
            )
        except Exception as e:
            return pb2.GetProcessesResponse(
                status="failure", error_message=f"Unexpected error: {str(e)}"
            )


def serve(collector_config):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_SpawnerServiceServicer_to_server(
        SpawnerService(collector_config), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server started on port 50051")
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        server.stop(0)
