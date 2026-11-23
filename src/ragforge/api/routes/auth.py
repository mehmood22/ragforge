from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.api.auth import CurrentUserDep
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.models.user import User
from ragforge.repositories.user_repository import UserRepository
from ragforge.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from ragforge.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

SessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(
        repository=UserRepository(session),
        session=session,
    )


ServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    service: ServiceDep,
) -> ApiResponse[UserResponse]:
    user = await service.register(payload)

    return success_response(
        data=UserResponse.model_validate(user),
        message="Registration successful",
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
)
async def login(
    payload: LoginRequest,
    service: ServiceDep,
) -> ApiResponse[TokenResponse]:
    token = await service.login(payload)

    return success_response(
        data=token,
        message="Login successful",
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
)
async def get_me(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ApiResponse[UserResponse]:
    user = await session.get(User, current_user.id)

    if user is None or not user.is_active:
        # Normally handled by CurrentUserDep.
        # This also protects against account changes
        # between the dependency check and this query.
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="User account is unavailable",
        )

    return success_response(
        data=UserResponse.model_validate(user),
        message="Current user retrieved successfully",
    )
