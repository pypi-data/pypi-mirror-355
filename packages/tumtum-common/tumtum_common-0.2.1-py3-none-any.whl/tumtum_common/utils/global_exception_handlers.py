"""This module contains the global exception handlers for the FastAPI application."""

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from exceptions import CodeException
import logging

logger: logging.Logger = logging.getLogger(__name__)


async def code_exception_handler(ex: CodeException):
    """Handle CodeException.
    
    Args:
        ex (CodeException): The CodeException instance.
        
    Returns:
        JSONResponse: A JSON response with the error message and status code.
    """

    logger.exception(f"CODE EXCEPTION: {ex.status_code} | {ex.message}")

    return JSONResponse(
        status_code=ex.status_code,
        content={"error": ex.message},
    )

async def pydantic_validation_exception_handler(ex: RequestValidationError):
    """Handle RequestValidationError.
    
    Args:
        ex (RequestValidationError): The RequestValidationError instance.
        
    Returns:
        JSONResponse: A JSON response with the error message and status code.
    """

    logger.exception(f"VALIDATION EXCEPTION: {ex.errors} | {ex.__traceback__}")

    return JSONResponse(
        status_code=404,
        content={"error": "Validation failed"},
    )
