from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ragforge.api.auth import (
    create_access_token,
    get_current_user,
    verify_access_token,
)
from ragforge.core.config import get_settings


def test_create_and_verify_access_token():
    user_id = uuid4()

    token = create_access_token(user_id)
    current_user = verify_access_token(token)

    assert current_user.id == user_id


def test_token_contains_expected_claims():
    settings = get_settings()
    user_id = uuid4()

    token = create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
    )

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_expired_token_is_rejected():
    settings = get_settings()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "type": "access",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)

    assert exc.value.status_code == 401


def test_wrong_secret_is_rejected():
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "access",
        },
        "completely-different-signing-secret-123456",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)

    assert exc.value.status_code == 401


def test_invalid_token_type_is_rejected():
    settings = get_settings()

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "type": "refresh",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_bearer_token_with_active_user():
    user_id = uuid4()
    token = create_access_token(user_id)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    session = AsyncMock()
    session.get.return_value = MagicMock(is_active=True)

    current_user = await get_current_user(
        credentials,
        session,
    )

    assert current_user.id == user_id
    session.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_disabled_user_is_rejected():
    user_id = uuid4()
    token = create_access_token(user_id)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    session = AsyncMock()
    session.get.return_value = MagicMock(is_active=False)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials, session)

    assert exc.value.status_code == 401
