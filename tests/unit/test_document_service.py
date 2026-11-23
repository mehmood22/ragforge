from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ragforge.core.exceptions import DocumentNotFoundException
from ragforge.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_document_not_found_for_other_user() -> None:
    repository = AsyncMock()
    session = AsyncMock()

    document_id = uuid4()
    owner_id = uuid4()

    repository.get_owned.return_value = None

    service = DocumentService(
        repository=repository,
        session=session,
    )

    with pytest.raises(DocumentNotFoundException):
        await service.get_document(
            document_id=document_id,
            owner_id=owner_id,
        )

    repository.get_owned.assert_awaited_once_with(
        document_id=document_id,
        owner_id=owner_id,
    )


@pytest.mark.asyncio
async def test_list_documents_filters_by_owner() -> None:
    repository = AsyncMock()
    session = AsyncMock()
    owner_id = uuid4()

    repository.list_owned.return_value = []

    service = DocumentService(
        repository=repository,
        session=session,
    )

    result = await service.list_documents(
        owner_id=owner_id,
        limit=10,
        offset=0,
    )

    assert result == []
    repository.list_owned.assert_awaited_once_with(
        owner_id=owner_id,
        limit=10,
        offset=0,
    )
