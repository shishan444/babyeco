"""API v1 package initialization."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.children import router as children_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(children_router, prefix="/children", tags=["Children"])

__all__ = ["router"]
