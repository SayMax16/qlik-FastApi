from fastapi import APIRouter, Depends, Path, HTTPException, Query
from typing import Optional
from src.api.services.app_service import AppService
from src.api.core.dependencies import get_app_service, verify_api_key
from src.api.core.config import settings

router = APIRouter()

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
