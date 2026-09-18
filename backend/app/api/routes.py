from fastapi import APIRouter, HTTPException

from app.db import get_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", message="Sahayak backend is running")


@router.get("/health/db")
def health_db():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "ok", "database": "connected"}