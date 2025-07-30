"""Caching annotations."""

from fastapi import Depends
from typing import Annotated
from .clients import RedisClient, get_redis_client

RedisClientAnnotation = Annotated[
    RedisClient,
    Depends(get_redis_client)
]

