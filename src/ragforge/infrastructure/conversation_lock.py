from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from hashlib import blake2b
from uuid import UUID

from sqlalchemy import text

from ragforge.core.exceptions import ConflictException
from ragforge.infrastructure.database import engine


def conversation_lock_key(conversation_id: UUID) -> int:
    """Create a stable signed 64-bit PostgreSQL lock key."""
    digest = blake2b(
        conversation_id.bytes,
        digest_size=8,
        person=b"ragforge",
    ).digest()

    return int.from_bytes(digest, byteorder="big", signed=True)


@asynccontextmanager
async def conversation_lock(
    conversation_id: UUID,
) -> AsyncIterator[None]:
    """Prevent simultaneous processing of one conversation."""
    key = conversation_lock_key(conversation_id)

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": key},
        )

        acquired = result.scalar_one()

        if not acquired:
            raise ConflictException(
                "Conversation is already processing a request. Please retry shortly."
            )

        try:
            yield
        finally:
            await connection.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": key},
            )
