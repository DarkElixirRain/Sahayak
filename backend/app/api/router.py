"""Central API router aggregating all route modules."""

from fastapi import APIRouter

from app.api.routes import health, knowledge, system

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(knowledge.router)