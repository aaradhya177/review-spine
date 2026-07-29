from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.observability.logging import configure_logging
from app.webhook_receiver import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.settings = settings
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is not None:
        configure_logging(settings.log_level)

    app = FastAPI(
        title=(settings.app_name if settings else "Review Spine"),
        version="0.1.0",
        lifespan=lifespan,
    )

    if settings is not None:
        app.state.settings = settings
        app.dependency_overrides[get_settings] = lambda: settings

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        active_settings = getattr(app.state, "settings", None) or get_settings()
        return {
            "status": "ok",
            "service": active_settings.app_name,
            "environment": active_settings.app_env,
        }

    app.include_router(webhook_router)
    return app


app = create_app()
