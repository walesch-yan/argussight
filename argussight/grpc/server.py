import grpc
from concurrent import futures
import time
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock
import json

from argussight.core.spawner import Spawner, ProcessError

class SpawnerService(pb2_grpc.SpawnerServiceServicer):
    def __init__(self, shared_dict: DictProxy, lock: Lock):
        self.spawner = Spawner(shared_dict, lock)

    def StartProcesses(self, request, context):
        try:
            process_dicts = [
                {
                    'name': process.name,
                    'type': process.type,
                    'args': [json.loads(arg) for arg in process.args]
                }
                for process in request.processes
            ]
            self.spawner.start_processes(process_dicts)
            return pb2.StartProcessesResponse(status="success")
        except ProcessError as e:
            return pb2.StartProcessesResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.StartProcessesResponse(status="failure", error_message=f"Unexpected error: {str(e)}")

    def TerminateProcesses(self, request, context):
        try:
            self.spawner.terminate_processes(request.names)
            return pb2.TerminateProcessesResponse(status="success")
        except ProcessError as e:
            return pb2.TerminateProcessesResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.TerminateProcessesResponse(status="failure", error_message=f"Unexpected error: {str(e)}")

    def ManageProcesses(self, request, context):
        try:
            self.spawner.manage_processes(request.name, request.message)
            return pb2.ManageProcessesResponse(status="success")
        except ProcessError as e:
            return pb2.ManageProcessesResponse(status="failure", error_message=str(e))
        except Exception as e:
            return pb2.ManageProcessesResponse(status="failure", error_message=f"Unexpected error: {str(e)}")

def serve(shared_dict: DictProxy, lock: Lock):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_SpawnerServiceServicer_to_server(
        SpawnerService(shared_dict, lock), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        server.stop(0)