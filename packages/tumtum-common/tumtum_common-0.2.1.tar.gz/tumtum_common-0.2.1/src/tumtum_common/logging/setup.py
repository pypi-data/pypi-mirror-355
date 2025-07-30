"""Setup logging for the application."""

from logging.handlers import TimedRotatingFileHandler
from fastapi.logger import logger as fastapi_logger
from datetime import datetime
import logging
import sys
import os

def setup_logging(logs_level: str, logs_filename: str, logs_format: str) -> None:
    """Set up logging for the application.
    
    Args:
        logs_level (str): Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        logs_filename (str): Filename for the log file, with a date placeholder (e.g., 'app-{date}.log').
        logs_format (str): Format string for log messages.
    Raises:
        ValueError: If the logs_level / logs_format / gols_filename is not a valid.
        FileNotFoundError: If the logs_filename directory does not exist or cannot be created.
    """

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()

    formatter = logging.Formatter(logs_format)

    # Simple console/stdout logging
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    # File logging handler
    os.makedirs("logs", exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        logs_filename.format(date=datetime.now().strftime('%Y-%m-%d')),
        when="midnight",
        interval=1,
        backupCount=7
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logs_level)
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    fastapi_logger.handlers = logger.handlers
    fastapi_logger.setLevel(logs_level)