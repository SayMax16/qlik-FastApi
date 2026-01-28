"""Dependency injection setup for FastAPI endpoints."""

from typing import Annotated

from fastapi import Depends

from src.api.core.config import Settings, get_settings

from src.api.clients.qlik_engine import QlikEngineClient
from src.api.clients.qlik_repository import QlikRepositoryClient


def get_settings_dependency() -> Settings:
    """Dependency to get application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]


def get_qlik_engine_client(
    settings: SettingsDep = None,
) -> QlikEngineClient:
    """Dependency to get Qlik Engine client."""
    if settings is None:
        settings = get_settings()
    return QlikEngineClient(settings)


def get_qlik_repository_client(
    settings: SettingsDep = None,
) -> QlikRepositoryClient:
    """Dependency to get Qlik Repository client."""
    if settings is None:
        settings = get_settings()
    return QlikRepositoryClient(settings)


# Service factories
def get_app_service() -> "AppService":
    """Get AppService instance."""
    from src.api.services.app_service import AppService
    from src.api.repositories.app_repository import AppRepository

    return AppService(
        app_repository=AppRepository(
            repository_client=get_qlik_repository_client(),
            engine_client=get_qlik_engine_client()
        )
    )


def get_data_service() -> "DataService":
    """Get DataService instance."""
    from src.api.services.data_service import DataService
    from src.api.repositories.data_repository import DataRepository
    from src.api.repositories.app_repository import AppRepository

    return DataService(
        data_repository=DataRepository(
            engine_client=get_qlik_engine_client()
        ),
        app_repository=AppRepository(
            repository_client=get_qlik_repository_client(),
            engine_client=get_qlik_engine_client()
        )
    )
