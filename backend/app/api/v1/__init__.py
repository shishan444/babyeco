"""API v1 package initialization."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.children import router as children_router
from app.api.v1.points import router as points_router
from app.api.v1.tasks import router as tasks_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(children_router, prefix="/children", tags=["Children"])
router.include_router(points_router, prefix="/points", tags=["Points"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])

__all__ = ["router"]
