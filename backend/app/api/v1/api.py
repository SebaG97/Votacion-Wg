from fastapi import APIRouter

from app.api.v1.endpoints import auth, habilitaciones, health, padron, votaciones, votos

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(padron.router, tags=["padron"])
api_router.include_router(habilitaciones.router, tags=["habilitaciones"])
api_router.include_router(votos.router, tags=["votos"])
api_router.include_router(votaciones.public_router, tags=["votaciones"])
api_router.include_router(votaciones.router, tags=["votaciones"])
