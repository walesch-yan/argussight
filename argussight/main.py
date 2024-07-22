import argparse
import multiprocessing

from argussight.core.config import get_config_from_dict
from argussight.core.collector import Collector
from argussight.grpc.server import serve

def parse_args() -> None:
    opt_parser = argparse.ArgumentParser(description="mxcube argussight")

    opt_parser.add_argument(
        "-c",
        "--config",
        dest="config_file_path",
        help="Configuration file path",
        default="",
    )

    opt_parser.add_argument(
        "-hs",
        "--host",
        dest="host",
        help="host of the redis server",
        default="localhost",
    )

    opt_parser.add_argument(
        "-p",
        "--port",
        dest="port",
        help="port of redis server",
        default="6379",
    )

    opt_parser.add_argument(
        "-ch",
        "--channel",
        dest="channel",
        help="channel of the video-stream",
        default='video-streamer',
    )

    return opt_parser.parse_args()

def run() -> None:
    args = parse_args()

    config = get_config_from_dict(
        {
            "redis":{
                "host": args.host,
                "port": args.port,
                "channel": args.channel,
            }
        }
    )

    manager = multiprocessing.Manager()
    lock = multiprocessing.Lock()

    shared_dict = manager.dict()

    with lock:
        shared_dict["frame_number"] = -1

    collector = Collector(config, shared_dict, lock)

    collection_process = multiprocessing.Process(target=collector.start)
    server = multiprocessing.Process(target=serve, args=(shared_dict, lock))

    try:
        collection_process.start()
        server.start()

        collection_process.join()
        server.join()

    except KeyboardInterrupt:
        print("Terminating processes...")
        collection_process.terminate()
        server.terminate()

        collection_process.join()
        server.join()
        print("Termination completed")

if __name__ == "__main__":
    run()