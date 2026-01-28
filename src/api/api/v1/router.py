"""API v1 router configuration."""

from fastapi import APIRouter

from src.api.api.v1.endpoints import health, apps, data

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(apps.router, tags=["Apps"])
api_router.include_router(data.router, tags=["Data"])
