from fastapi import APIRouter, Depends
from src.api.schemas.common import HealthResponse
from src.api.services.app_service import AppService
from src.api.core.dependencies import get_app_service
from src.api.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(
    app_service: AppService = Depends(get_app_service)
):
    """Check API and Qlik connection health."""
    qlik_status = await app_service.check_connection()

    return HealthResponse(
        status="healthy" if qlik_status else "degraded",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        qlik_connected=qlik_status
    )
