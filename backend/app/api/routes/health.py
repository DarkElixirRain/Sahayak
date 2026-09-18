"""Health check endpoints."""

from fastapi import APIRouter

from app.db.session import check_database
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="sahayak-api")


@router.get("/db", response_model=DatabaseHealthResponse)
def health_db() -> DatabaseHealthResponse:
    check_database()
    return DatabaseHealthResponse(status="ok", database="connected")