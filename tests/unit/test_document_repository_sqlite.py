import pytest
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from ragforge.models import Base
from ragforge.models.document import Document
from ragforge.repositories.document_repository import DocumentRepository


@pytest.mark.asyncio
async def test_repository_create_and_get_with_sqlite() -> None:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            repository = DocumentRepository(session)

            document = Document(
                name="SQLite Test",
                source_type="pdf",
                status="pending",
                chunk_count=0,
            )

            await repository.create(document)
            await session.commit()

            result = await repository.get_by_id(document.id)

            assert result is not None
            assert result.name == "SQLite Test"

    finally:
        await engine.dispose()
