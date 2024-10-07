import json
from google.protobuf.any_pb2 import Any


def pack_to_any(value):
    any_obj = Any()

    if isinstance(value, str):
        any_obj.value = value.encode("utf-8")

    elif isinstance(value, (dict, list)):
        json_value = json.dumps(value)
        any_obj.value = json_value.encode("utf-8")

    # Handle other cases if needed (like numbers, custom types, etc.)
    else:
        raise TypeError(f"Unsupported type: {type(value)}")

    return any_obj


def unpack_from_any(any_obj):
    try:
        # Attempt to decode as a UTF-8 string (could be a simple string or JSON)
        decoded_value = any_obj.value.decode("utf-8")

        # If it looks like JSON, parse it
        try:
            return json.loads(decoded_value)
        except json.JSONDecodeError:
            return decoded_value

    except Exception as e:
        raise ValueError(f"Failed to unpack value from Any: {e}")
