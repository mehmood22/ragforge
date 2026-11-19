from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ragforge.models.document import (
    DocumentStatus,
    SourceType,
)
from ragforge.schemas.document import DocumentCreate
from ragforge.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
)


@pytest.mark.asyncio
async def test_create_document() -> None:
    repository = AsyncMock()
    session = AsyncMock()

    repository.create.side_effect = lambda document: document

    service = DocumentService(
        repository=repository,
        session=session,
    )

    payload = DocumentCreate(
        name="Roaming Policy",
        source_type=SourceType.PDF,
    )

    document = await service.create_document(payload)

    assert document.name == "Roaming Policy"
    assert document.source_type == "pdf"
    assert document.status == DocumentStatus.PENDING.value
    assert document.chunk_count == 0

    repository.create.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_document_not_found() -> None:
    repository = AsyncMock()
    session = AsyncMock()

    repository.get_by_id.return_value = None

    service = DocumentService(
        repository=repository,
        session=session,
    )

    with pytest.raises(DocumentNotFoundError):
        await service.get_document(uuid4())


@pytest.mark.asyncio
async def test_create_document_rolls_back_on_error() -> None:
    repository = AsyncMock()
    session = AsyncMock()

    repository.create.side_effect = RuntimeError("Database write failed")

    service = DocumentService(
        repository=repository,
        session=session,
    )

    payload = DocumentCreate(
        name="Failure Test",
        source_type=SourceType.TEXT,
    )

    with pytest.raises(RuntimeError):
        await service.create_document(payload)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
