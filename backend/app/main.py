from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router
from app.db import close_pool, init_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url:
        init_pool()
    yield
    close_pool()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered voice-based rights and safety assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "message": "Welcome to the Sahayak backend",
        "docs": "/docs",
    }