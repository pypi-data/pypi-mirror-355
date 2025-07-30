"""Database core."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import entities
from fastapi import FastAPI
from dataclasses import dataclass
import asyncio
import logging
from typing import AsyncGenerator

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database credentials."""
    db_url: str
    db_username: str
    db_password: str
    db_host: str
    db_name: str

@dataclass
class PoolConfig:
    """Pool configuration."""
    pool_size: int = 10
    max_overflows: int = 1
    pool_timeout: int = 10
    pool_recycle: int = 10
    pool_pre_ping: int = 10
    echo: bool = False
    echo_pool: bool = False
    hide_parameters: bool = True

@dataclass
class ConnectionConfig:
    """Other parameters."""
    max_connections_retries: int = 5
    retry_delay: int = 3


async def init_engine(
    app: FastAPI, 
    db_config: DatabaseConfig,
    pool_config: PoolConfig,
    connection_config: ConnectionConfig
):
    """Initialize the database engine.
    
    Args:
        app: The FastAPI app.
        db_config: The database configuration.
        pool_config: The pool configuration.
        connection_config: The connection configuration.
    """

    logger.info(f"Initializing database engine")

    if (
        not db_config.db_url
        or not db_config.db_username
        or not db_config.db_password
        or not db_config.db_host
        or not db_config.db_name
    ):
        raise ValueError("Invalid database configuration")

    connection_url = db_config.db_url.format(
        username=db_config.db_username,
        password=db_config.db_password,
        host=db_config.db_host,
        bd_name=db_config.db_name
    )

    app.state.db_engine = create_async_engine(
        connection_url,
        pool_size=pool_config.pool_size,
        max_overflow=pool_config.max_overflows,
        pool_timeout=pool_config.pool_timeout,
        pool_recycle=pool_config.pool_recycle,
        pool_pre_ping=pool_config.pool_pre_ping,
        echo=pool_config.echo,
        echo_pool=pool_config.echo_pool,
        hide_parameters=pool_config.hide_parameters
    )

    app.state.db_session_maker = sessionmaker(
        app.state.db_engine, 
        class_=AsyncSession
    )

    logger.info(f"Database engine initialized")


    # Check if the database is reachable
    logger.info(f"Checking if the database is reachable")
    for _ in range(connection_config.max_connections_retries):
        try:
            async with app.state.db_engine.connect() as conn:
                await conn.execute("SELECT 1")

            logger.info(f"Database is reachable")
            break
        except Exception as e:
            logger.error(f"Failed to connect to the database: {e}")
            await asyncio.sleep(connection_config.retry_delay)

async def get_db_session(app: FastAPI) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session.
    
    Args:
        app: The FastAPI app.
    """

    async with app.state.db_session_maker() as session:
        yield session

