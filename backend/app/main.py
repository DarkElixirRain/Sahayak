"""Sahayak API application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import APP_NAME, APP_VERSION, settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.session import close_pool, init_pool

logger = get_logger(__name__)

setup_logging(settings.log_level)


def create_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.database_url:
            try:
                init_pool()
                logger.info("Database connection pool initialized")
            except Exception:
                logger.exception("Failed to initialize database connection pool")
        else:
            logger.warning("DATABASE_URL is not set; database features disabled")
        yield
        close_pool()

    app = FastAPI(
        title=APP_NAME,
        description="AI-powered voice-based rights and safety assistant for Nepal",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": APP_NAME,
        "message": "Welcome to the Sahayak backend",
        "docs": "/docs",
    }