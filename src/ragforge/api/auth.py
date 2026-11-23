from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import get_settings
from ragforge.infrastructure.database import get_db_session
from ragforge.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(token: str) -> CurrentUser:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={
                "require": ["sub", "iat", "exp"],
            },
        )

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        user_id = UUID(payload["sub"])

        return CurrentUser(id=user_id)

    except (PyJWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_user = verify_access_token(credentials.credentials)

    user = await session.get(User, current_user.id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


CurrentUserDep = Annotated[
    CurrentUser,
    Depends(get_current_user),
]
