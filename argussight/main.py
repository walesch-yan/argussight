import argparse
import multiprocessing

from argussight.core.config import get_config_from_dict, SaveFormat
from argussight.core.collector import Collector
from argussight.core.spawner import Spawner

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

    opt_parser.add_argument(
        "-qml",
        "--queue-max-length",
        dest='queue_max_length',
        help="maximal number of frames saved in the queue",
        default="200",
    )

    opt_parser.add_argument(
        "-s",
        "--save",
        dest="save_folder",
        help="path to folder to save the queue",
        default='./logs/queue',
    )

    opt_parser.add_argument(
        "-f",
        "--format",
        dest="format",
        help="Format to save the queue to. Allowed values: 'video', 'frames' or 'both'",
        default='both',
    )

    return opt_parser.parse_args()

def run() -> None:
    args = parse_args()

    if args.format not in SaveFormat._value2member_map_:
        raise ValueError(f"Invalid value: {args.format}. Allowed values are: {[value.value for value in SaveFormat]}")

    config = get_config_from_dict(
        {
            "redis":{
                "host": args.host,
                "port": args.port,
                "channel": args.channel,
            },
            "queue":{
                "save_folder": args.save_folder,
                "max_length": args.queue_max_length,
                "save_format": args.format 
            }
        }
    )

    manager = multiprocessing.Manager()
    lock = multiprocessing.Lock()

    shared_dict = manager.dict()

    with lock:
        shared_dict["frame_number"] = -1

    collector = Collector(config, shared_dict, lock)
    spawner = Spawner(shared_dict, lock)

    collection_process = multiprocessing.Process(target=collector.start)
    spawning_process = multiprocessing.Process(target=spawner.run)

    try:
        collection_process.start()
        spawning_process.start()

        collection_process.join()
        spawning_process.join()

    except KeyboardInterrupt:
        print("Terminating processes...")
        collection_process.terminate()
        spawning_process.terminate()

        collection_process.join()
        spawning_process.join()
        print("Termination completed")

if __name__ == "__main__":
    run()