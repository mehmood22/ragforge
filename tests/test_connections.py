import asyncio

import pytest
from sqlalchemy import text

from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.infrastructure.database import SessionFactory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_connection() -> None:
    async with SessionFactory() as session:
        result = await session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chroma_connection() -> None:
    client = get_chroma_client()

    heartbeat = await asyncio.to_thread(client.heartbeat)

    assert isinstance(heartbeat, int)
    assert heartbeat > 0
