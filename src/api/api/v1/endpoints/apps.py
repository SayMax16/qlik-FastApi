from fastapi import APIRouter, Depends, Path, HTTPException, Query
from typing import Optional, List
from src.api.services.app_service import AppService
from src.api.core.dependencies import get_app_service, verify_api_key
from src.api.core.config import settings

router = APIRouter()

# IMPORTANT: More specific routes must come BEFORE generic routes
# This application_status route must be defined before the generic {table_name} route

@router.get("/apps/{app_name}/tables/application_status/data")
async def get_application_status_data(
    app_name: str = Path(..., description="Application name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=10000, description="Rows per page"),
    yearmonth: Optional[str] = Query(None, description="Filter by YearMonth (format: 2026.01 or 2026-01), supports multiple values separated by comma"),
    app_service: AppService = Depends(get_app_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Get application status data with optional YearMonth filtering.

    This endpoint retrieves data from the application_status table and supports
    filtering by YearMonth field using Qlik selections. The YearMonth field
    exists in the app but may not be in the table itself.

    **Examples:**

    Get all data (no filtering):
    ```
    GET /api/v1/apps/Stock/tables/application_status/data?page=1&page_size=100
    ```

    Filter by single month:
    ```
    GET /api/v1/apps/Stock/tables/application_status/data?page=1&page_size=100&yearmonth=2024-01
    ```

    Filter by multiple months:
    ```
    GET /api/v1/apps/Stock/tables/application_status/data?page=1&page_size=100&yearmonth=2024-01,2024-02,2024-03
    ```

    **Response format:**
    ```json
    {
      "object_id": "UWDJj",
      "app_id": "...",
      "app_name": "Stock",
      "data": [
        {
          "Field1": "Value1",
          "Field2": "Value2",
          ...
        }
      ],
      "pagination": {
        "page": 1,
        "page_size": 100,
        "total_rows": 150,
        "total_pages": 2,
        "has_next": true,
        "has_previous": false
      }
    }
    ```
    """
    table_name = "application_status"

    # Check app access
    if not settings.can_access_app(api_key, app_name):
        raise HTTPException(
            status_code=403,
            detail=f"Your API key does not have access to app '{app_name}'"
        )

    # Check table access
    if not settings.can_access_table(api_key, app_name, table_name):
        raise HTTPException(
            status_code=403,
            detail=f"Your API key does not have access to table '{table_name}' in app '{app_name}'"
        )

    # Get object ID for this table
    object_id = settings.get_object_id_for_table(app_name, table_name)
    if not object_id:
        raise HTTPException(
            status_code=404,
            detail=f"No object mapping found for table '{table_name}' in app '{app_name}'"
        )

    # Get bookmark ID for this table
    # The bookmark pre-filters the data to 3 months for fast retrieval
    bookmark_id = settings.get_bookmark_id(app_name, table_name)

    # application_status uses the regular table object (UWDJj)
    # Apply bookmark FIRST to filter the data before creating the hypercube
    data = await app_service.get_object_data(
        app_name=app_name,
        object_id=object_id,
        page=page,
        page_size=page_size,
        filters={},  # No client-side filtering
        selections={},  # No Qlik selections - rely on bookmark
        bookmark_id=bookmark_id  # Applied FIRST to filter the data
    )

    return data


@router.get("/apps/{app_name}/tables/{table_name}/data")
async def get_table_data_with_measures(
    app_name: str = Path(..., description="Application name"),
    table_name: str = Path(..., description="Table name (e.g., stock_qty)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=10000, description="Rows per page"),
    factory: Optional[str] = Query(None, description="Filter by factory (PRCTR field)"),
    warehouse: Optional[str] = Query(None, description="Filter by warehouse (LGORT field)"),
    app_service: AppService = Depends(get_app_service),
    api_key: str = Depends(verify_api_key)
):
    """
    Get actual data from a table with dimensions and measures.

    This endpoint retrieves actual data rows where each row contains
    all dimension values and calculated measure values.

    **Example:**
    ```
    GET /api/v1/apps/Stock/tables/stock_qty/data?page=1&page_size=10
    ```

    **With filters:**
    ```
    GET /api/v1/apps/Stock/tables/stock_qty/data?page=1&page_size=10&factory=1203&warehouse=P210
    ```

    **Response format:**
    ```json
    {
      "data": [
        {
          "MATNR": "000000001000000000",
          "Название материалов": "Замес д. ПВХ профилей PE",
          "База Код": "1203",
          "Название завода": "Производство ПВХ профилей",
          "Склад": "P210",
          "СвобИспользЗапас": 234.22,
          "Базовая ЕИ": "KG"
        }
      ],
      "pagination": {...}
    }
    ```
    """
    # Check app access
    if not settings.can_access_app(api_key, app_name):
        raise HTTPException(
            status_code=403,
            detail=f"Your API key does not have access to app '{app_name}'"
        )

    # Check table access
    if not settings.can_access_table(api_key, app_name, table_name):
        raise HTTPException(
            status_code=403,
            detail=f"Your API key does not have access to table '{table_name}' in app '{app_name}'"
        )

    # Get object ID for this table
    object_id = settings.get_object_id_for_table(app_name, table_name)
    if not object_id:
        raise HTTPException(
            status_code=404,
            detail=f"No object mapping found for table '{table_name}' in app '{app_name}'"
        )

    # Build filters dictionary
    # Map query parameters to actual Qlik field names
    filters = {}
    if factory:
        filters['PRCTR'] = factory  # PRCTR is the factory field in Qlik
    if warehouse:
        filters['LGORT'] = warehouse  # LGORT is the warehouse field in Qlik

    data = await app_service.get_object_data(app_name, object_id, page, page_size, filters)
    return data
