"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.children import router as children_router
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Clean up resources


app = FastAPI(
    title="BabyEco API",
    description="BabyEco Account System Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(children_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
