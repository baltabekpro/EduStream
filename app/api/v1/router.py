from fastapi import APIRouter
from app.api.v1.endpoints import auth, materials, ai, ocr, analytics

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(materials.router)
api_router.include_router(ai.router)
api_router.include_router(ocr.router)
api_router.include_router(analytics.router)
