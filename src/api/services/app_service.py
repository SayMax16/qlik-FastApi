"""App service module for application operations."""

import asyncio
from typing import List

from src.api.services.base import BaseService
from src.api.repositories.app_repository import AppRepository
from src.api.schemas.app import AppInfo, TableInfo
from src.api.core.exceptions import AppNotFoundException


class AppService(BaseService):
    """Service for app operations.

    Provides business logic for managing Qlik Sense applications,
    including listing apps, retrieving table information, and
    health checking connections.
    """

    def __init__(self, app_repository: AppRepository):
        """Initialize the AppService.

        Args:
            app_repository: Repository for app data access operations.
        """
        self.app_repo = app_repository

    async def list_apps(self) -> List[AppInfo]:
        """List all available applications.

        Retrieves all configured Qlik Sense applications from the
        repository and returns them as AppInfo models.

        Returns:
            List of AppInfo models containing app metadata.

        Raises:
            Exception: If there's an error connecting to Qlik Sense.
        """
        # Execute blocking repository call in thread pool
        apps = await asyncio.to_thread(self.app_repo.list_all_apps)

        # Convert raw dictionaries to Pydantic models
        return [AppInfo(**app) for app in apps]

    async def list_tables(self, app_name: str) -> List[TableInfo]:
        """List all tables in an application.

        Retrieves all tables/data models within a specific Qlik Sense
        application and returns them as TableInfo models.

        Args:
            app_name: Name of the application to retrieve tables from.

        Returns:
            List of TableInfo models containing table metadata.

        Raises:
            AppNotFoundException: If the specified app doesn't exist.
            Exception: If there's an error connecting to Qlik Sense.
        """
        # Validate app exists and get app ID
        app_id = self.app_repo.get_app_id_by_name(app_name)
        if not app_id:
            raise AppNotFoundException(app_name)

        # Execute blocking repository call in thread pool
        tables = await asyncio.to_thread(self.app_repo.get_app_tables, app_id)

        # Convert raw dictionaries to Pydantic models
        return [TableInfo(**table) for table in tables]

    async def check_connection(self) -> bool:
        """Check Qlik connection health.

        Tests the connection to Qlik Sense server to ensure it's
        accessible and responding properly.

        Returns:
            True if connection is healthy, False otherwise.
        """
        # Execute blocking repository call in thread pool
        return await asyncio.to_thread(self.app_repo.check_connection)
