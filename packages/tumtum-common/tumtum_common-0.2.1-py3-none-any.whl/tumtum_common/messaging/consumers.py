"""Common package for TumTum messaging consumers."""

from aiokafka import AIOKafkaConsumer
from abc import ABC, abstractmethod
import json
import asyncio
from contextlib import asynccontextmanager
import logging
from pydantic import BaseModel, ValidationError
from typing import Optional, Type

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    """Abstract base class for consumers."""
    
    @abstractmethod
    async def start(self):
        """Start the consumer."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the consumer."""
        pass

    @abstractmethod
    async def consume(self):
        """Consume messages from the subscribed topics."""
        pass


class KafkaBaseConsumer(BaseConsumer, ABC):
    def __init__(
        self,
        name: str,
        topic: str,
        message_class: Type[BaseModel],
        bootstrap_servers: str,
        group_id: str,
        connection_retries: int = 5,
        connection_retry_delay: int = 3,
        consume_task_cancel_timeout: int = 5,
        consumer_stop_timeout: int = 5
    ):
        """Base class for Kafka consumers.
        
        Args:
            _name (str): _Name of the consumer.
            topic (str): Topic to subscribe to.
            message_class (type, optional): Class for deserializing messages. Defaults to None.
        """

        if not topic:
            raise ValueError("Topic must be specified for Kafka consumer.")
        if not bootstrap_servers:
            raise ValueError("Bootstrap servers must be specified for Kafka consumer.")
        if not group_id:
            raise ValueError("Group ID must be specified for Kafka consumer.")
        if not message_class:
            raise ValueError("Message class must be specified for Kafka consumer.")
        if not name:
            name = f"KafkaConsumer-{topic}"

        self._kafka_consumer_instance = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        self._topic: str = topic
        self._name: str = name
        self._message_class: Type[BaseModel] = message_class
        self._consume_task: Optional[asyncio.Task] = None
        self._connection_retries: int = connection_retries
        self._connection_retry_delay: int = connection_retry_delay
        self._consume_task_cancel_timeout: int = consume_task_cancel_timeout
        self._consumer_stop_timeout: int = consumer_stop_timeout

    @property
    def topic(self):
        """Return the topic to which the consumer is subscribed."""
        return self._topic
    
    @property
    def name(self):
        """Return the _name of the consumer."""
        return self._name

    @property
    def message_class(self):
        """Return the class used for deserializing messages."""
        return self._message_class

    @property
    def connection_retries(self):
        """Return the number of connection retries."""
        return self._connection_retries

    @property
    def connection_retry_delay(self):
        """Return the delay between connection retries."""
        return self._connection_retry_delay

    @property
    def consume_task_cancel_timeout(self):
        """Return the timeout for cancelling the consume task."""
        return self._consume_task_cancel_timeout

    @property
    def consumer_stop_timeout(self):
        """Return the timeout for stopping the consumer."""
        return self._consumer_stop_timeout

    async def start(self):
        """Start the consumer and subscribe to topics."""

        logger.info(f"Kafka: starting consumer '{self._name}' for topics: {self._topic}")
        
        for _ in range(self._connection_retries):
            try:
                await self._kafka_consumer_instance.start()
                logger.info(f"Kafka: consumer '{self._name}' started")
                break
            except Exception as e:
                logger.error(f"Error starting Kafka consumer '{self._name}': {e}")
                await asyncio.sleep(self._connection_retry_delay)
        else:
            return

        try:
            self._consume_task = asyncio.create_task(self.consume())
        except Exception as e:
            logger.error(f"Error creating consume task for Kafka consumer '{self._name}': {e}")
            await self.stop()

    async def stop(self):
        """Stop the consumer."""
        
        logger.info(f"Kafka: stopping consumer '{self._name}'")

        if self._consume_task and not self._consume_task.done():
            self._consume_task.cancel()

            # Wait for the consume task to complete
            try:
                await asyncio.wait_for(self._consume_task, timeout=self._consume_task_cancel_timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            
        # Hard stop the consumer
        try:
            await asyncio.wait_for(self._kafka_consumer_instance.stop(), timeout=self._consumer_stop_timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while stopping consumer '{self._name}'")

        logger.info(f"Kafka: consumer '{self._name}' stopped")

    async def consume(self):
        """Consume messages from the subscribed topics."""
        try:
            logger.info(f"Kafka consumer '{self._name}' started consuming messages")
            
            async for message in self._kafka_consumer_instance:
                try:
                    msg_obj = self._message_class(**message.value)
                    await self.process_message(msg_obj)
                except ValidationError as e:
                    logger.error(f"Invalid message format: {e}")
                except Exception as e:
                    logger.error(f"Processing error: {e}", exc_info=True)
                    
        except asyncio.CancelledError:
            logger.info(f"Consumer '{self._name}' was cancelled")
        except Exception as e:
            logger.error(f"Consumer '{self._name}' failed: {e}", exc_info=True)
        finally:
            logger.info(f"Kafka consumer '{self._name}' stopped consuming messages")

    @abstractmethod
    async def process_message(self, message: BaseModel):
        """Process the consumed message."""
        pass


@asynccontextmanager
async def manage_consumers(*consumers: BaseConsumer):
    """Manage lifecycle of multiple Kafka consumers."""
    try:
        await asyncio.gather(*(consumer.start() for consumer in consumers))
        yield
    finally:
        await asyncio.gather(*(consumer.stop() for consumer in consumers))

