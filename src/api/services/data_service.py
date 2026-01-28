"""Data service module for data retrieval operations."""

import asyncio
from typing import Dict, Any

from src.api.services.base import BaseService
from src.api.repositories.data_repository import DataRepository
from src.api.repositories.app_repository import AppRepository
from src.api.schemas.data import TableDataResponse, DataFilterParams
from src.api.schemas.common import PaginationParams, PaginationMeta
from src.api.core.exceptions import AppNotFoundException, TableNotFoundException


class DataService(BaseService):
    """Service for data operations.

    Provides business logic for retrieving and filtering table data
    from Qlik Sense applications with pagination support.
    """

    def __init__(
        self,
        data_repository: DataRepository,
        app_repository: AppRepository
    ):
        """Initialize the DataService.

        Args:
            data_repository: Repository for data retrieval operations.
            app_repository: Repository for app validation operations.
        """
        self.data_repo = data_repository
        self.app_repo = app_repository

    async def get_table_data(
        self,
        app_name: str,
        table_name: str,
        pagination: PaginationParams,
        filters: DataFilterParams
    ) -> TableDataResponse:
        """Get paginated table data with filtering.

        Retrieves data from a specific table in a Qlik Sense application
        with support for pagination and filtering.

        Args:
            app_name: Name of the application containing the table.
            table_name: Name of the table to retrieve data from.
            pagination: Pagination parameters (page, page_size).
            filters: Optional filter parameters for data filtering.

        Returns:
            TableDataResponse containing paginated data and metadata.

        Raises:
            AppNotFoundException: If the specified app doesn't exist.
            TableNotFoundException: If the specified table doesn't exist.
            Exception: If there's an error retrieving data from Qlik Sense.
        """
        # Step 1: Validate app exists
        app_id = self.app_repo.get_app_id_by_name(app_name)
        if not app_id:
            raise AppNotFoundException(app_name)

        # Step 2: Get data from repository (blocking, so use thread pool)
        # This ensures the blocking Qlik Sense API calls don't block the event loop
        result = await asyncio.to_thread(
            self.data_repo.get_table_data,
            app_id=app_id,
            table_name=table_name,
            page=pagination.page,
            page_size=pagination.page_size,
            filters=filters
        )

        # Step 3: Build pagination metadata
        # Calculate total pages using ceiling division
        total_pages = (
            result["total_records"] + pagination.page_size - 1
        ) // pagination.page_size

        pagination_meta = PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_records=result["total_records"],
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )

        # Step 4: Return response with Pydantic model
        return TableDataResponse(
            app_name=app_name,
            table_name=table_name,
            data=result["data"],
            pagination=pagination_meta,
            metadata=result.get("metadata", {})
        )
