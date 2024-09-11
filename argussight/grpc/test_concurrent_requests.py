import grpc
import argussight.grpc.argus_service_pb2 as pb2
import argussight.grpc.argus_service_pb2_grpc as pb2_grpc
import threading
import json
import time


def make_request(stub, request_data):
    try:
        print(f"Running {request_data}")
        response = stub.ManageProcesses(
            pb2.ManageProcessesRequest(
                name="initial test",
                order="print",
                wait_time=5,
                args=[json.dumps(request_data)],
            )
        )
        print(
            f"Received response: {response.status, response.error_message} for {request_data}"
        )
    except grpc.RpcError as e:
        print(f"RPC error: {e} on {request_data}")


def test_concurrent_requests(stub, num_requests):
    threads = []
    for i in range(num_requests):
        time.sleep(0.5)
        thread = threading.Thread(target=make_request, args=(stub, f"request {i}"))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = pb2_grpc.SpawnerServiceStub(channel)
        test_concurrent_requests(stub, 50)  # Adjust the number of requests as needed


if __name__ == "__main__":
    run()
