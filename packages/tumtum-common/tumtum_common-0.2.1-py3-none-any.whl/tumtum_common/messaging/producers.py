"""Module for Kafka producers in the TumTum messaging system."""

import logging
from typing import Type, Optional
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer
from abc import ABC, abstractmethod
from fastapi import FastAPI
import asyncio
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class BaseProducer(ABC):
    """Abstract base class for producers."""

    @abstractmethod
    async def start(self):
        """Start the producer."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the producer."""
        pass

    @abstractmethod
    async def produce(self, message: BaseModel):
        """Produce a message to the topic."""
        pass


class KafkaBaseProducer(BaseProducer, ABC):
    """Base class for Kafka producers."""
        
    def __init__(
        self,
        name: str,
        bootstrap_servers: str,
        message_class: Type[BaseModel],
        connection_retries: int = 3,
        connection_retry_delay: int = 5
    ):
        """Initialize the Kafka producer.
        
        Args:
            name (str): Name of the producer.
            bootstrap_servers (str): Kafka bootstrap servers.
            message_class (Type[BaseModel]): Class for serializing messages.
            connection_retries (int): Number of retries to connect to Kafka.
            connection_retry_delay (int): Delay between connection retries in seconds.
        """

        if not name:
            raise ValueError("Name must be specified for Kafka producer.")
        if not bootstrap_servers:
            raise ValueError("Bootstrap servers must be specified for Kafka producer.")
        if not message_class or not issubclass(message_class, BaseModel):
            raise ValueError("Message class must be specified and must inherit from BaseModel.")

        self._name = name
        self._bootstrap_servers = bootstrap_servers
        self._message_class = message_class
        self._connection_retries = connection_retries
        self._connection_retry_delay = connection_retry_delay
        self._producer: Optional[AIOKafkaProducer] = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers
        )

    async def start(self):
        """Start the Kafka producer."""
        if not self._producer or self._producer._closed:
            logger.info(f"Starting Kafka producer '{self._name}'...")

            for _ in range(self._connection_retries):
                try:
                    await self._producer.start()
                    logger.info(f"Kafka producer '{self._name}' started successfully.")
                    return
                except Exception as e:
                    logger.warning(f"Failed to start Kafka producer '{self._name}': {e}")
                    await asyncio.sleep(self._connection_retry_delay)

    async def stop(self):
        """Stop the Kafka producer."""
        if self._producer and not self._producer._closed:
            logger.info(f"Stopping Kafka producer '{self._name}'...")
            await self._producer.stop()
            logger.info(f"Kafka producer '{self._name}' stopped.")
        else:
            logger.warning(f"Kafka producer '{self._name}' is already stopped or not initialized.")

    async def produce(self, topic: str, message: BaseModel):
        """Produce a message to the specified Kafka topic.
        
        Args:
            topic (str): The Kafka topic to which the message will be sent.
            message (BaseModel): The message to be sent, must be an instance of BaseModel.
        
        Raises:
            RuntimeError: If the producer is not initialized or if the producer is closed.
        """
        if not self._producer or self._producer._closed:
            raise RuntimeError("Producer not initialized or already closed.")
        
        try:
            await self._producer.send_and_wait(
                topic,
                value=json.dumps(message.to_dict()).encode('utf-8')
            )
            logger.info(f"Message sent to topic '{topic}': {message.to_dict()}")
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")


@asynccontextmanager
async def manage_producers(app: FastAPI, producers: dict[str, BaseProducer] = None):
    """Context manager to manage multiple producers.
    
    Args:
        app: The FastAPI app.
        producers: The producers to be managed.
    
    Yields:
        tuple: A tuple of producers that are started and ready for use.

    Raises:
        ValueError: If no producers are provided.
        ValueError: If the producer value type is not 'BaseProducer'.
        ValueError: If the producer key type is not 'str'.
    """

    for key, value in producers.items():
        if not isinstance(value, BaseProducer):
            raise ValueError(f"Invalid producer value type: {type(value)}. Can support only 'BaseProducer' type.")
        if not isinstance(key, str):
            raise ValueError(f"Invalid producer key type: {type(key)}. Can support only 'str' type.")
        
    app.state.producers = producers

    try:
        for producer in producers:
            await producer.start()
        yield
    finally:
        for producer in producers:
            await producer.stop()

def get_producer(app: FastAPI, producer_name: str) -> BaseProducer:
    """Get a producer.
    
    Args:
        app: The FastAPI app.
        producer_name: The name of the producer.
    """
    return app.state.producers[producer_name]

