"""Caching clients for TumTum services."""

from redis.asyncio import Redis
from models.entities import User
from .models import UserSession
from abc import ABC, abstractmethod
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import json

logger = logging.getLogger(__name__)


class BaseCacheClient(ABC):
    """Base cache client."""

    @abstractmethod
    async def get(self, key: str) -> str:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ex: int = None) -> None:
        """Set a value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        pass


class RedisClient(BaseCacheClient):
    """Redis client for TumTum services."""

    def __init__(self, host: str, port: int, password: str = None):
        """Initialize the Redis client.
        
        Args:
            host: The host of the Redis server.
            port: The port of the Redis server.
            password: The password of the Redis server.
        """
        logger.info(f"Initializing Redis client with host: {host}, port: {port}, password: '*******'")

        if not password:
            self._redis_client: Redis = Redis(host=host, port=port)
        else:
            self._redis_client: Redis = Redis(host=host, port=port, password=password)

        logger.info(f"Redis client initialized")

    async def get(self, key: str) -> str:
        """Get a value from Redis.
        
        Args:
            key: The key to get the value from.

        Returns:
            The value from Redis.
        """
        return await self._redis_client.get(key)

    async def set(self, key: str, value: str, ex: int = None) -> None:
        """Set a value in Redis.
        
        Args:
            key: The key to set the value to.
            value: The value to set.
            ex: The expiration time of the value.
        """
        await self._redis_client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        """Delete a value from Redis.
        
        Args:
            key: The key to delete the value from.
        """
        await self._redis_client.delete(key)

    async def close(self) -> None:
        """Close the Redis client."""
        await self._redis_client.close()

    
@asynccontextmanager
async def manage_redis_client(app: FastAPI, host: str, port: int, password: str = None):
    """Manage the Redis client.
    
    Args:
        app: The FastAPI app.
        host: The host of the Redis server.
        port: The port of the Redis server.
        password: The password of the Redis server.
    
    Raises:
        ValueError: If host or port are not provided.
    """

    if not host or not port:
        raise ValueError("Host and port are required")

    if not password:
        logger.info(f"Initializing Redis client with host: {host}, port: {port}")

        app.state.redis_client = RedisClient(
            host=host,
            port=port
        )
    else:
        logger.info(f"Initializing Redis client with host: {host}, port: {port}, password: '*******'")

        app.state.redis_client = RedisClient(
            host=host,
            port=port,
            password=password
        )

    logger.info(f"Redis client initialized")

    try:
        yield
    finally:
        await app.state.redis_client.close()

def get_redis_client(app: FastAPI) -> RedisClient:
    """Get a Redis client.
    
    Args:
        app: The FastAPI app.

    Returns:
        The Redis client.
    """
    return app.state.redis_client

