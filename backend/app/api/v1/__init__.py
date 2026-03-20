"""API v1 package initialization."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.children import router as children_router
from app.api.v1.points import router as points_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.exchange import router as exchange_router
from app.api.v1.entertainment import router as entertainment_router
from app.api.v1.ai import router as ai_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(children_router, prefix="/children", tags=["Children"])
router.include_router(points_router, prefix="/points", tags=["Points"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
router.include_router(exchange_router, prefix="/exchange", tags=["Exchange"])
router.include_router(entertainment_router, prefix="/entertainment", tags=["Entertainment"])
router.include_router(ai_router, prefix="/ai", tags=["AI"])

__all__ = ["router"]