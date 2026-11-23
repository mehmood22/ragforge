from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.api.auth import create_access_token
from ragforge.core.config import get_settings
from ragforge.models.user import User
from ragforge.repositories.user_repository import UserRepository
from ragforge.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("ragforge-dummy-password-for-timing")


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        session: AsyncSession,
    ) -> None:
        self.repository = repository
        self.session = session

    async def register(self, payload: RegisterRequest) -> User:
        password_hash = await run_in_threadpool(
            password_hasher.hash,
            payload.password,
        )

        user = User(
            email=str(payload.email),
            password_hash=password_hash,
            is_active=True,
        )

        try:
            created = await self.repository.create(user)
            await self.session.commit()
            return created

        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            ) from exc

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.repository.get_by_email(str(payload.email))

        stored_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH

        valid_password = await run_in_threadpool(
            password_hasher.verify,
            payload.password,
            stored_hash,
        )

        if user is None or not valid_password or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        settings = get_settings()

        return TokenResponse(
            access_token=create_access_token(user.id),
            expires_in=settings.jwt_expire_minutes * 60,
        )
