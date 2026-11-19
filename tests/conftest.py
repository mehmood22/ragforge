from collections.abc import AsyncGenerator

import pytest_asyncio

from ragforge.infrastructure.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_db_engine() -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()
