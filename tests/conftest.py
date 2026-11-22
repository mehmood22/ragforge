import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from ragforge.infrastructure.database import engine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(autouse=True)
def mock_checkpointer(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_saver = MagicMock()
    fake_saver.setup = AsyncMock()

    @asynccontextmanager
    async def fake_from_conn_string(*args, **kwargs):
        yield fake_saver

    monkeypatch.setattr(
        "ragforge.main.AsyncPostgresSaver.from_conn_string",
        fake_from_conn_string,
    )


@pytest_asyncio.fixture(autouse=True)
async def _dispose_db_engine() -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()
