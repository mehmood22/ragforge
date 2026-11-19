from fastapi import FastAPI

from ragforge.api.routes.documents import (
    router as documents_router,
)
from ragforge.api.routes.health import router as health_router
from ragforge.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )

    app.include_router(
        health_router,
        prefix="/api/v1",
    )

    app.include_router(
        documents_router,
        prefix="/api/v1",
    )

    return app


app = create_app()
