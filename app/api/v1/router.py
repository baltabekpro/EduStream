from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, 
    dashboard,
    users,
    ai_swagger,
    ocr_swagger,
    analytics_swagger,
    materials_swagger,
    share
)

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(ai_swagger.router)
api_router.include_router(ocr_swagger.router)
api_router.include_router(analytics_swagger.router)
api_router.include_router(materials_swagger.router)
api_router.include_router(share.router)
