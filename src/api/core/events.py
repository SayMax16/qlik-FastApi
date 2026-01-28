"""Application lifecycle events (startup and shutdown)."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.core.config import settings
from src.api.core.exceptions import CertificateError, ConfigurationError

logger = logging.getLogger(__name__)


async def check_certificates() -> None:
    """Verify that all required certificates exist."""
    if not settings.cert_files_exist:
        cert_path, key_path, root_path = settings.get_cert_paths()
        missing = []
        if not cert_path.exists():
            missing.append(str(cert_path))
        if not key_path.exists():
            missing.append(str(key_path))
        if not root_path.exists():
            missing.append(str(root_path))

        raise CertificateError(
            message="Required certificate files not found",
            details={"missing_files": missing},
        )
    logger.info("All certificate files found")


async def validate_configuration() -> None:
    """Validate application configuration on startup."""
    logger.info("Validating configuration...")

    # Check required settings
    if not settings.QLIK_SENSE_HOST:
        raise ConfigurationError("QLIK_SENSE_HOST is required")

    if not settings.QLIK_USER_DIRECTORY:
        raise ConfigurationError("QLIK_USER_DIRECTORY is required")

    if not settings.QLIK_USER_ID:
        raise ConfigurationError("QLIK_USER_ID is required")

    # Check certificates if SSL verification is enabled
    if settings.QLIK_VERIFY_SSL:
        await check_certificates()

    logger.info("Configuration validated successfully")


async def startup_event() -> None:
    """Execute startup tasks."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Qlik Sense host: {settings.QLIK_SENSE_HOST}")

    # Validate configuration
    await validate_configuration()

    # TODO: Initialize connection pools, caches, etc.
    # TODO: Test connectivity to Qlik Sense (optional health check)

    logger.info("Application startup complete")


async def shutdown_event() -> None:
    """Execute shutdown tasks."""
    logger.info("Shutting down application...")

    # TODO: Close connection pools
    # TODO: Cleanup resources
    # TODO: Close WebSocket connections

    logger.info("Application shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    await startup_event()

    yield

    # Shutdown
    await shutdown_event()
