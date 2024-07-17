import grpc
from concurrent import futures
import time
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import Lock

# Import your Spawner class here
from argussight.core.spawner import Spawner

class SpawnerService(pb2_grpc.SpawnerServiceServicer):
    def __init__(self, shared_dict: DictProxy, lock: Lock):
        self.spawner = Spawner(shared_dict, lock)

    def StartProcesses(self, request, context):
        self.spawner.load_config()
        self.spawner.start_processes()
        return pb2.StartProcessesResponse(message="Processes started successfully.")

    def TerminateProcesses(self, request, context):
        self.spawner.terminate_processes(request.names)
        return pb2.TerminateProcessesResponse(message="Processes terminated successfully.")

    def ManageProcesses(self, request, context):
        self.spawner.manage_processes()
        return pb2.ManageProcessesResponse(message="Process management started successfully.")

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