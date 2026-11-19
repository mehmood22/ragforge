import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ragforge.core.exceptions import AppException
from ragforge.core.responses import ApiError, ApiResponse

logger = logging.getLogger(__name__)


def error_response(
    status_code: int,
    message: str,
    code: str,
    details: dict | list | None = None,
) -> JSONResponse:
    body = ApiResponse[None](
        success=False,
        message=message,
        data=None,
        error=ApiError(
            code=code,
            details=details,
        ),
    )

    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        message=exc.message,
        code=exc.error_code,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(item) for item in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return error_response(
        status_code=422,
        message="Request validation failed",
        code="VALIDATION_ERROR",
        details=details,
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled application exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return error_response(
        status_code=500,
        message="An unexpected error occurred",
        code="INTERNAL_SERVER_ERROR",
    )
