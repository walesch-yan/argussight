import time

import grpc

import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
from argussight.core.video_processes.savers.video_saver import SaveFormat
from argussight.grpc.helper_functions import pack_to_any


def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = pb2_grpc.SpawnerServiceStub(channel)

    # Get status
    print("Sending get Status request")
    try:
        response = stub.GetProcesses(pb2.GetProcessesRequest())
    except Exception as e:
        print(e)
    print(response.status, response.error_message)
    print(response.running_processes, response.available_process_types)

    time.sleep(5)

    # Change settings
    print("Sending Change settings request")
    try:
        response = stub.ChangeSettings(
            pb2.ChangeSettingsRequest(
                name="Saver", settings={"personnal_folder": pack_to_any("test2")}
            )
        )
    except Exception as e:
        print(e)
    print(response.status, response.error_message)

    time.sleep(5)

    # Get status
    print("Sending get Status request")
    try:
        response = stub.GetProcesses(pb2.GetProcessesRequest())
    except Exception as e:
        print(e)
    print(response.status, response.error_message)
    print(response.running_processes, response.available_process_types)

    time.sleep(5)

    # Manage process
    print("Sending manage process request")
    try:
        response = stub.ManageProcesses(
            pb2.ManageProcessesRequest(name="Saver", command="save")
        )
    except Exception as e:
        print(e)
    print(response.status, response.error_message)


if __name__ == "__main__":
    run()
