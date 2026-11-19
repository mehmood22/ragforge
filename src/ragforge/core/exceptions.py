from typing import Any

HTTP_STATUS_CODES: dict[str, int] = {
    "bad_request": 400,
    "not_found": 404,
    "conflict": 409,
    "unprocessable_entity": 422,
    "service_unavailable": 503,
}


class AppException(Exception):
    status_code: int = HTTP_STATUS_CODES["bad_request"]
    error_code: str = "APPLICATION_ERROR"
    default_message: str = "Application error"

    def __init__(
        self,
        message: str | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


class NotFoundException(AppException):
    status_code = HTTP_STATUS_CODES["not_found"]
    error_code = "NOT_FOUND"
    default_message = "Resource not found"


class ValidationException(AppException):
    status_code = HTTP_STATUS_CODES["unprocessable_entity"]
    error_code = "VALIDATION_ERROR"
    default_message = "Invalid request"


class ConflictException(AppException):
    status_code = HTTP_STATUS_CODES["conflict"]
    error_code = "CONFLICT"
    default_message = "Resource conflict"


class ExternalServiceException(AppException):
    status_code = HTTP_STATUS_CODES["service_unavailable"]
    error_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "An external service is unavailable"


class DocumentNotFoundException(NotFoundException):
    error_code = "DOCUMENT_NOT_FOUND"
    default_message = "Document not found"
