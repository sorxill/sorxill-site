from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.v1.routers import health, projects
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    get_logger(__name__).info("api.startup", env=settings.app_env, version=settings.app_version)
    yield
    get_logger(__name__).info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="sorxill.ru API",
        version=settings.app_version,
        docs_url=None if settings.is_production else "/docs",
        lifespan=lifespan,
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(projects.router)
    return app


app = create_app()
