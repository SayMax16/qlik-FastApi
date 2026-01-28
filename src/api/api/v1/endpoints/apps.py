from fastapi import APIRouter, Depends, Path
from src.api.schemas.app import AppListResponse, TableListResponse
from src.api.services.app_service import AppService
from src.api.core.dependencies import get_app_service

router = APIRouter()

@router.get("/apps", response_model=AppListResponse)
async def list_apps(
    app_service: AppService = Depends(get_app_service)
):
    """List all available applications."""
    apps = await app_service.list_apps()
    return AppListResponse(apps=apps)

@router.get("/apps/{app_name}/tables", response_model=TableListResponse)
async def list_tables(
    app_name: str = Path(..., description="Application name"),
    app_service: AppService = Depends(get_app_service)
):
    """List all tables in an application."""
    tables = await app_service.list_tables(app_name)
    return TableListResponse(app_name=app_name, tables=tables)
