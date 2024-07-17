import grpc
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.SpawnerServiceStub(channel)

    # Start processes
    response = stub.StartProcesses(pb2.StartProcessesRequest())
    print(response.message)

    # Terminate processes
    response = stub.TerminateProcesses(pb2.TerminateProcessesRequest(names=['process1', 'process2']))
    print(response.message)

    # Manage processes
    response = stub.ManageProcesses(pb2.ManageProcessesRequest())
    print(response.message)

if __name__ == '__main__':
    run()
