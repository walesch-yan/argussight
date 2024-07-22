import grpc
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
import json
import time
from argussight.core.video_processes.video_saver import SaveFormat

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = pb2_grpc.SpawnerServiceStub(channel)

    processes = [
        pb2.ProcessInfo(
            name='Remote Test',
            type='flow_detection',
            args=[json.dumps([500,500,300,450])]
        )
    ]

    # Start processes
    print("Sending start request for flow_detection")
    response = stub.StartProcesses(pb2.StartProcessesRequest(processes=processes))
    print(response.status, response.error_message)

    print("Waiting for 5 seconds...")
    time.sleep(5)

    print("Sending handle request for test process")
    response = stub.ManageProcesses(pb2.ManageProcessesRequest(name='Remote Test', order='change_roi', wait_time=5, args=[json.dumps([200, 200, 400, 500])]))
    print(response.status, response.error_message)

    print("Waiting for 5 seconds...")
    time.sleep(5)

    print("Sending handle request for test process")
    response = stub.ManageProcesses(pb2.ManageProcessesRequest(name='Remote Test', order='change_roi', wait_time=5, args=[json.dumps([500, 500, 300, 450])]))
    print(response.status, response.error_message)

    print("Waiting for 5 seconds...")
    time.sleep(5)

    print("Sending handle request for saving process")
    response = stub.ManageProcesses(pb2.ManageProcessesRequest(name='Saver', order='save', wait_time=30, args=[json.dumps(SaveFormat.BOTH.value), json.dumps("./test")]))
    print(response.status, response.error_message)

    print("Waiting 5 seconds...")
    time.sleep(5)

    print("Sending termination request for test")
    response = stub.TerminateProcesses(pb2.TerminateProcessesRequest(names=["Remote Test"]))
    print(response.status, response.error_message)

if __name__ == '__main__':
    run()
