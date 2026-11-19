from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ragforge.core.config import get_settings


def create_engine_instance() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


engine: AsyncEngine = create_engine_instance()

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def dispose_engine() -> None:
    await engine.dispose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        yield session
