from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    details: dict | list | None = None


class ApiResponse[T](BaseModel):
    success: bool
    message: str
    data: T | None = None
    error: ApiError | None = None


def success_response[T](
    data: T,
    message: str = "Operation successful",
) -> ApiResponse[T]:
    return ApiResponse[T](
        success=True,
        message=message,
        data=data,
    )
