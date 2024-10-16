import grpc
from concurrent import futures
import time
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
from argussight.grpc.helper_functions import pack_to_any, unpack_from_any

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
            self.spawner.manage_process(
                request.name,
                request.command,
                {},
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
                settings = {}
                for key, setting in process["settings"].items():
                    settings[key] = pack_to_any(setting)
                running_dict[name] = pb2.RunningProcessDictionary(
                    type=process["type"],
                    commands=process["commands"],
                    settings=settings,
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

    def ChangeSettings(self, request, context):
        try:
            settings = {}
            for key, any_object in request.settings.items():
                settings[key] = unpack_from_any(any_object)
            self.spawner.manage_process(request.name, "settings", [settings])
            return pb2.ChangeSettingsResponse(status="success")
        except ProcessError as e:
            return pb2.ChangeSettingsResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.ChangeSettingsResponse(status="failure", error_message=str(e))


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
