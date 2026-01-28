"""Error handling middleware for FastAPI."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.core.exceptions import QlikSenseAPIException
from src.api.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


async def qlik_sense_exception_handler(
    request: Request, exc: QlikSenseAPIException
) -> JSONResponse:
    """Handle custom Qlik Sense API exceptions."""
    logger.error(
        f"QlikSenseAPIException: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "details": exc.details,
        },
    )

    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"errors": exc.errors()},
    )

    error_response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": exc.errors()},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    logger.warning(
        f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}",
    )

    error_response = ErrorResponse(
        error="HTTPException",
        message=str(exc.detail),
        status_code=exc.status_code,
        details=None,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions."""
    logger.exception(
        f"Unhandled exception on {request.url.path}",
        exc_info=exc,
    )

    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"error": str(exc)} if logger.level == logging.DEBUG else None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Add all exception handlers to the FastAPI application."""
    app.add_exception_handler(QlikSenseAPIException, qlik_sense_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
