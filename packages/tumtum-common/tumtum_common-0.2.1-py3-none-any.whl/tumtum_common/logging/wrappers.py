"""Logging decorators for function entrance and exit with debug, info, and error levels."""

from functools import wraps
import logging
import inspect

def log_entrance_debug(logger: logging.Logger):
    """Decorator to log function entrance and exit with debug level.

    Args:
        logger (logging.Logger): Logger instance to use for logging.
    Returns:
        function: Wrapped function with logging.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger.debug(f"Function {func.__name__} entrance | args {args} ; kwargs {kwargs}")
                result = await func(*args, **kwargs)
                logger.debug(f"Function {func.__name__} exit | Result {result}")
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                logger.debug(f"Function {func.__name__} entrance | args {args} ; kwargs {kwargs}")
                result = func(*args, **kwargs)
                logger.debug(f"Function {func.__name__} exit | Result {result}")
                return result

            return sync_wrapper
    return decorator

def log_entrance_info(logger: logging.Logger):
    """Decorator to log function entrance and exit with info level.
    
    Args:
        logger (logging.Logger): Logger instance to use for logging.
    Returns:
        function: Wrapped function with logging.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger.info(f"Function {func.__name__} entrance | args {args} ; {kwargs}")
                result = await func(*args, **kwargs)
                logger.info(f"Function {func.__name__} exit | Result {result}")
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                logger.info(f"Function {func.__name__} entrance | args {args} ; {kwargs}")
                result = func(*args, **kwargs)
                logger.info(f"Function {func.__name__} exit | Result {result}")
                return result
            
            return sync_wrapper
    return decorator

def log_entrance_error(logger: logging.Logger):
    """Decorator to log function entrance and exit with error level.
    
    Args:
        logger (logging.Logger): Logger instance to use for logging.
    Returns:
        function: Wrapped function with logging.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger.error(f"Function {func.__name__} entrance | args {args} ; {kwargs}")
                result = await func(*args, **kwargs)
                logger.error(f"Function {func.__name__} exit | Result {result}")
                return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                logger.error(f"Function {func.__name__} entrance | args {args} ; {kwargs}")
                result = func(*args, **kwargs)
                logger.error(f"Function {func.__name__} exit | Result {result}")
                return result
            
            return sync_wrapper
    return decorator
