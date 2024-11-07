import Levenshtein
from typing import Union
import socket


def find_close_key(d: dict, key: str, max_distance: int = 3) -> Union[str, None]:
    """Return first key in dict whose Levenshtein distance to key is <= max_distance"""
    min_distance = float("inf")
    closest_key = None

    for dict_key in d:
        distance = Levenshtein.distance(key, dict_key)
        if distance < min_distance:
            min_distance = distance
            closest_key = dict_key

    if min_distance <= max_distance:
        return closest_key

    return None


def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # Optional: set a short timeout for connection attempt
        result = s.connect_ex(("localhost", port))
        return result != 0  # If result is non-zero, port is free


def find_free_port(start_port=9000):
    port = start_port
    while not is_port_free(port):
        port += 1
    return port
