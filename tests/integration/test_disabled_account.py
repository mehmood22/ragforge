from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from ragforge.infrastructure.database import SessionFactory
from ragforge.main import create_app
from ragforge.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
async def test_disabled_user_cannot_use_existing_token() -> None:
    app = create_app()
    email = f"disabled-{uuid4().hex}@example.com"
    user_id: UUID | None = None

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        try:
            registered = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongTestPassword123!",
                },
            )
            assert registered.status_code == 201, registered.text

            user_id = UUID(registered.json()["data"]["id"])

            logged_in = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": "StrongTestPassword123!",
                },
            )
            assert logged_in.status_code == 200, logged_in.text

            token = logged_in.json()["data"]["access_token"]

            headers = {"Authorization": f"Bearer {token}"}

            before = await client.get(
                "/api/v1/auth/me",
                headers=headers,
            )
            assert before.status_code == 200

            # Disable the account directly in the test database.
            async with SessionFactory.begin() as session:
                user = await session.get(User, user_id)
                assert user is not None
                user.is_active = False

            # The same JWT must now be rejected.
            after = await client.get(
                "/api/v1/auth/me",
                headers=headers,
            )
            assert after.status_code == 401

        finally:
            if user_id is not None:
                async with SessionFactory.begin() as session:
                    await session.execute(delete(User).where(User.id == user_id))
