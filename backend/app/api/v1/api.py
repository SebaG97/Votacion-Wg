from fastapi import APIRouter

from app.api.v1.endpoints import habilitaciones, health, padron

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(padron.router, tags=["padron"])
api_router.include_router(habilitaciones.router, tags=["habilitaciones"])
