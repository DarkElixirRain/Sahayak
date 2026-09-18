"""External API contracts for system-level endpoints."""

from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    service: str
    environment: str
    version: str