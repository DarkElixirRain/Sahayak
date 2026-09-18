"""System-level endpoints. Never expose secrets, keys, or infrastructure detail."""

from fastapi import APIRouter

from app.core.config import APP_NAME, APP_VERSION, settings
from app.schemas.system import SystemInfoResponse

SERVICE_NAME = "sahayak-api"

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
def system_info() -> SystemInfoResponse:
    return SystemInfoResponse(
        service=SERVICE_NAME,
        environment=settings.app_env,
        version=APP_VERSION,
    )