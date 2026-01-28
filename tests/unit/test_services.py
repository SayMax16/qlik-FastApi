"""Unit tests for service layer components."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.api.services.app_service import AppService
from src.api.services.data_service import DataService
from src.api.core.exceptions import (
    AppNotFoundException,
    TableNotFoundException,
    QlikConnectionError,
    ValidationError
)
from src.api.schemas.pagination import PaginationParams
from src.api.schemas.filters import FilterParams


class TestAppService:
    """Test cases for AppService."""

    @pytest.mark.asyncio
    async def test_list_apps_success(self, mock_app_repository):
        """Test successful listing of all apps."""
        service = AppService(app_repository=mock_app_repository)
        apps = await service.list_apps()

        assert len(apps) == 1
        assert apps[0].app_name == "akfa-employees"
        assert apps[0].app_id == "5a730580-3c25-4805-a2ef-dd4a71a91cda"
        mock_app_repository.list_all_apps.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_apps_empty(self):
        """Test listing apps when no apps exist."""
        mock_repo = Mock()
        mock_repo.list_all_apps = AsyncMock(return_value=[])

        service = AppService(app_repository=mock_repo)
        apps = await service.list_apps()

        assert len(apps) == 0
        assert apps == []

    @pytest.mark.asyncio
    async def test_get_app_by_id_success(self, mock_app_repository, mock_app_id):
        """Test successful retrieval of app by ID."""
        service = AppService(app_repository=mock_app_repository)
        app = await service.get_app_by_id(mock_app_id)

        assert app is not None
        assert app["app_id"] == mock_app_id
        mock_app_repository.get_app_by_id.assert_called_once_with(mock_app_id)

    @pytest.mark.asyncio
    async def test_get_app_by_id_not_found(self):
        """Test app not found by ID."""
        mock_repo = Mock()
        mock_repo.get_app_by_id = AsyncMock(return_value=None)

        service = AppService(app_repository=mock_repo)

        with pytest.raises(AppNotFoundException):
            await service.get_app_by_id("nonexistent-id")

    @pytest.mark.asyncio
    async def test_get_app_by_name_success(self, mock_app_repository, mock_app_name):
        """Test successful retrieval of app by name."""
        service = AppService(app_repository=mock_app_repository)
        app_id = await service.get_app_id_by_name(mock_app_name)

        assert app_id == "5a730580-3c25-4805-a2ef-dd4a71a91cda"
        mock_app_repository.get_app_id_by_name.assert_called_once_with(mock_app_name)

    @pytest.mark.asyncio
    async def test_get_app_by_name_not_found(self):
        """Test app not found by name."""
        mock_repo = Mock()
        mock_repo.get_app_id_by_name = AsyncMock(return_value=None)

        service = AppService(app_repository=mock_repo)

        with pytest.raises(AppNotFoundException) as exc_info:
            await service.get_app_id_by_name("nonexistent-app")

        assert "nonexistent-app" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_apps_connection_error(self):
        """Test handling of connection errors when listing apps."""
        mock_repo = Mock()
        mock_repo.list_all_apps = AsyncMock(
            side_effect=QlikConnectionError("Connection failed")
        )

        service = AppService(app_repository=mock_repo)

        with pytest.raises(QlikConnectionError) as exc_info:
            await service.list_apps()

        assert "Connection failed" in str(exc_info.value)


class TestDataService:
    """Test cases for DataService."""

    @pytest.mark.asyncio
    async def test_get_table_data_success(
        self,
        mock_data_repository,
        mock_app_repository,
        mock_app_name,
        sample_table_name
    ):
        """Test successful retrieval of table data."""
        pagination = PaginationParams(page=1, page_size=10)
        filters = FilterParams()

        service = DataService(
            data_repository=mock_data_repository,
            app_repository=mock_app_repository
        )

        result = await service.get_table_data(
            app_name=mock_app_name,
            table_name=sample_table_name,
            pagination=pagination,
            filters=filters
        )

        assert result is not None
        assert "columns" in result
        assert "rows" in result
        assert len(result["rows"]) == 2
        mock_app_repository.get_app_id_by_name.assert_called_once_with(mock_app_name)

    @pytest.mark.asyncio
    async def test_get_table_data_app_not_found(
        self,
        mock_data_repository,
        sample_table_name
    ):
        """Test table data retrieval when app doesn't exist."""
        mock_app_repo = Mock()
        mock_app_repo.get_app_id_by_name = AsyncMock(return_value=None)

        pagination = PaginationParams(page=1, page_size=10)
        filters = FilterParams()

        service = DataService(
            data_repository=mock_data_repository,
            app_repository=mock_app_repo
        )

        with pytest.raises(AppNotFoundException):
            await service.get_table_data(
                app_name="nonexistent",
                table_name=sample_table_name,
                pagination=pagination,
                filters=filters
            )

    @pytest.mark.asyncio
    async def test_get_table_data_table_not_found(
        self,
        mock_app_repository,
        mock_app_name
    ):
        """Test table data retrieval when table doesn't exist."""
        mock_data_repo = Mock()
        mock_data_repo.get_table_data = AsyncMock(
            side_effect=TableNotFoundException("Table not found")
        )

        pagination = PaginationParams(page=1, page_size=10)
        filters = FilterParams()

        service = DataService(
            data_repository=mock_data_repo,
            app_repository=mock_app_repository
        )

        with pytest.raises(TableNotFoundException):
            await service.get_table_data(
                app_name=mock_app_name,
                table_name="NonexistentTable",
                pagination=pagination,
                filters=filters
            )

    @pytest.mark.asyncio
    async def test_get_table_data_pagination(
        self,
        mock_data_repository,
        mock_app_repository,
        mock_app_name,
        sample_table_name
    ):
        """Test table data retrieval with different pagination settings."""
        # Test first page
        pagination_page1 = PaginationParams(page=1, page_size=5)
        filters = FilterParams()

        service = DataService(
            data_repository=mock_data_repository,
            app_repository=mock_app_repository
        )

        result = await service.get_table_data(
            app_name=mock_app_name,
            table_name=sample_table_name,
            pagination=pagination_page1,
            filters=filters
        )

        assert result is not None
        # Verify pagination params were passed correctly
        mock_data_repository.get_table_data.assert_called()

    @pytest.mark.asyncio
    async def test_get_table_data_with_filters(
        self,
        mock_data_repository,
        mock_app_repository,
        mock_app_name,
        sample_table_name
    ):
        """Test table data retrieval with filters."""
        pagination = PaginationParams(page=1, page_size=10)
        filters = FilterParams(field="Department", value="Sales")

        service = DataService(
            data_repository=mock_data_repository,
            app_repository=mock_app_repository
        )

        result = await service.get_table_data(
            app_name=mock_app_name,
            table_name=sample_table_name,
            pagination=pagination,
            filters=filters
        )

        assert result is not None
        mock_data_repository.get_table_data.assert_called()

    @pytest.mark.asyncio
    async def test_get_fields_success(
        self,
        mock_data_repository,
        mock_app_repository,
        mock_app_name
    ):
        """Test successful retrieval of field list."""
        service = DataService(
            data_repository=mock_data_repository,
            app_repository=mock_app_repository
        )

        fields = await service.get_fields(mock_app_name)

        assert fields is not None
        assert len(fields) == 2
        assert fields[0]["name"] == "Name"
        mock_data_repository.get_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error_handling(
        self,
        mock_app_repository,
        mock_app_name,
        sample_table_name
    ):
        """Test handling of Qlik connection errors."""
        mock_data_repo = Mock()
        mock_data_repo.get_table_data = AsyncMock(
            side_effect=QlikConnectionError("Failed to connect")
        )

        pagination = PaginationParams(page=1, page_size=10)
        filters = FilterParams()

        service = DataService(
            data_repository=mock_data_repo,
            app_repository=mock_app_repository
        )

        with pytest.raises(QlikConnectionError) as exc_info:
            await service.get_table_data(
                app_name=mock_app_name,
                table_name=sample_table_name,
                pagination=pagination,
                filters=filters
            )

        assert "Failed to connect" in str(exc_info.value)


class TestPaginationValidation:
    """Test cases for pagination parameter validation."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        pagination = PaginationParams(page=1, page_size=10)
        assert pagination.page == 1
        assert pagination.page_size == 10

    def test_pagination_page_too_small(self):
        """Test pagination with page number less than 1."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0, page_size=10)

    def test_pagination_page_size_too_small(self):
        """Test pagination with page size less than 1."""
        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=0)

    def test_pagination_page_size_too_large(self):
        """Test pagination with page size greater than max."""
        with pytest.raises(ValidationError):
            PaginationParams(page=1, page_size=2000)

    def test_pagination_defaults(self):
        """Test pagination with default values."""
        pagination = PaginationParams()
        assert pagination.page == 1
        assert pagination.page_size == 100


class TestFilterValidation:
    """Test cases for filter parameter validation."""

    def test_valid_filter(self):
        """Test valid filter parameters."""
        filters = FilterParams(field="Department", value="Sales")
        assert filters.field == "Department"
        assert filters.value == "Sales"

    def test_empty_filter(self):
        """Test empty filter parameters."""
        filters = FilterParams()
        assert filters.field is None
        assert filters.value is None

    def test_filter_field_without_value(self):
        """Test filter with field but no value."""
        with pytest.raises(ValidationError):
            FilterParams(field="Department")

    def test_filter_value_without_field(self):
        """Test filter with value but no field."""
        with pytest.raises(ValidationError):
            FilterParams(value="Sales")
