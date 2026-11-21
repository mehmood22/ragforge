from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ragforge.api.routes.documents import router as documents_router
from ragforge.api.routes.health import router as health_router
from ragforge.api.routes.ingestion_jobs import (
    router as ingestion_jobs_router,
)
from ragforge.api.routes.uploads import router as uploads_router
from ragforge.core.config import get_settings
from ragforge.core.exceptions import AppException
from ragforge.core.handlers import (
    app_exception_handler as _app_exception_handler,
)
from ragforge.core.handlers import (
    error_response,
    unexpected_exception_handler,
)
from ragforge.core.handlers import (
    validation_exception_handler as _validation_exception_handler,
)
from ragforge.core.logging import configure_logging
from ragforge.core.middleware import RequestLoggingMiddleware


async def _handle_app_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, AppException)
    return await _app_exception_handler(request, exc)


async def _handle_validation_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return await _validation_exception_handler(request, exc)


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        code="HTTP_ERROR",
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        log_to_file=settings.log_to_file,
        log_dir=settings.log_dir,
        log_file_prefix=settings.log_file_prefix,
        log_backup_days=settings.log_backup_days,
    )

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=False,
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.add_exception_handler(AppException, _handle_app_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_exception)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_exception_handler)

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(uploads_router, prefix="/api/v1")
    app.include_router(ingestion_jobs_router, prefix="/api/v1")

    return app


app = create_app()
