from pydantic import BaseModel, Field
from typing import Union
from enum import Enum

class SaveFormat(Enum):
    VIDEO = 'video'
    FRAMES = 'frames'
    BOTH = 'both'

class RedisConfiguration(BaseModel):
    host: str = Field("localhost", description="redis host")
    port: int = Field(6379, description="redis port")
    channel: str = Field("video-streamer", description="redis-channel to publish stream")

class QueueConfiguration(BaseModel):
    save_folder: str = Field("./queue", description="folder where to save the queue")
    max_length: int = Field(200, description="maximal length of the queue")
    save_format: SaveFormat = Field('both', description="format for saving the queue")

class CollectorConfiguration(BaseModel):
    redis: RedisConfiguration
    queue: QueueConfiguration

def get_config_from_dict(config_data: dict) -> Union[CollectorConfiguration, None]:
    data = CollectorConfiguration(**config_data)
    return data
