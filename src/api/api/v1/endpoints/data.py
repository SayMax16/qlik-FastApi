from fastapi import APIRouter, Depends, Path, Query, HTTPException
from typing import Optional
from src.api.schemas.data import TableDataResponse, DataFilterParams
from src.api.services.data_service import DataService
from src.api.core.dependencies import get_data_service, verify_api_key
from src.api.core.config import settings


class PaginationData:
    """Simple pagination data holder."""
    def __init__(self, page: int, page_size: int):
        self.page = page
        self.page_size = page_size


router = APIRouter()

@router.get("/apps/{app_name}", response_model=TableDataResponse)
async def get_default_table_data(
    app_name: str = Path(..., description="Application name"),
    page: Optional[int] = Query(None, ge=1, description="Page number (omit for all data)"),
    page_size: int = Query(100, ge=1, le=10000, description="Items per page"),
    all_data: bool = Query(False, description="Set to true to get all data without pagination"),
    filter_field: Optional[str] = Query(None, description="Field to filter on"),
    filter_value: Optional[str] = Query(None, description="Filter value"),
    sort_field: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    data_service: DataService = Depends(get_data_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Get paginated data from the default table of a Qlik Sense app.

    **Example:**
    ```
    GET /api/v1/apps/afko?page=1&page_size=50
    ```

    **Get all data (no pagination):**
    ```
    GET /api/v1/apps/afko?all_data=true
    ```

    **With filtering:**
    ```
    GET /api/v1/apps/afko?page=1&page_size=50&filter_field=Department&filter_value=Sales
    ```

    **With sorting:**
    ```
    GET /api/v1/apps/afko?page=1&sort_field=EmployeeID&sort_order=desc
    ```
    """
    # Get the default table ID for this app
    table_id = settings.get_default_table_id(app_name)
    if not table_id:
        raise HTTPException(
            status_code=404,
            detail=f"No default table configured for app '{app_name}'"
        )

    # Handle all_data flag - use max allowed page size (10000)
    if all_data:
        page = 1
        page_size = 10000  # Qlik's max allowed page size
    elif page is None:
        page = 1  # Default to page 1 if not specified

    pagination = PaginationData(page=page, page_size=page_size)
    filters = DataFilterParams(
        filter_field=filter_field,
        filter_value=filter_value,
        sort_field=sort_field,
        sort_order=sort_order
    )

    result = await data_service.get_table_data(
        app_name=app_name,
        table_name=table_id,
        pagination=pagination,
        filters=filters
    )

    return result


@router.get("/apps/{app_name}/tables/{table_name}", response_model=TableDataResponse)
async def get_table_data(
    app_name: str = Path(..., description="Application name"),
    table_name: str = Path(..., description="Table name"),
    page: Optional[int] = Query(None, ge=1, description="Page number (omit for all data)"),
    page_size: int = Query(100, ge=1, le=10000, description="Items per page"),
    all_data: bool = Query(False, description="Set to true to get all data without pagination"),
    filter_field: Optional[str] = Query(None, description="Field to filter on"),
    filter_value: Optional[str] = Query(None, description="Filter value"),
    sort_field: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    data_service: DataService = Depends(get_data_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Get paginated data from a specific table in a Qlik Sense app.

    **Example:**
    ```
    GET /api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=50
    ```

    **Get all data (no pagination):**
    ```
    GET /api/v1/apps/akfa-employees/tables/Employees?all_data=true
    ```

    **With filtering:**
    ```
    GET /api/v1/apps/akfa-employees/tables/Employees?page=1&page_size=50&filter_field=Department&filter_value=Sales
    ```

    **With sorting:**
    ```
    GET /api/v1/apps/akfa-employees/tables/Employees?page=1&sort_field=EmployeeID&sort_order=desc
    ```
    """

    # Handle all_data flag - use max allowed page size (10000)
    if all_data:
        page = 1
        page_size = 10000  # Qlik's max allowed page size
    elif page is None:
        page = 1  # Default to page 1 if not specified

    pagination = PaginationData(page=page, page_size=page_size)
    filters = DataFilterParams(
        filter_field=filter_field,
        filter_value=filter_value,
        sort_field=sort_field,
        sort_order=sort_order
    )

    result = await data_service.get_table_data(
        app_name=app_name,
        table_name=table_name,
        pagination=pagination,
        filters=filters
    )

    return result
