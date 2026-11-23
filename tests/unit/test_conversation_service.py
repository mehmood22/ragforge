from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ragforge.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from ragforge.models.conversation import Conversation
from ragforge.services.conversation_service import (
    ConversationService,
)


@pytest.mark.asyncio
async def test_creates_new_conversation():
    repository = AsyncMock()
    session = AsyncMock()

    repository.get_owned.return_value = None
    session.get.return_value = None

    service = ConversationService(repository, session)

    conversation_id = uuid4()
    document_id = uuid4()
    owner_id = uuid4()

    result = await service.get_or_create(
        conversation_id=conversation_id,
        document_id=document_id,
        owner_id=owner_id,
        question="What is the refund policy?",
    )

    assert result.id == conversation_id
    assert result.owner_id == owner_id
    assert result.document_id == document_id
    assert result.title == "What is the refund policy?"

    repository.create.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reuses_existing_conversation():
    repository = AsyncMock()
    session = AsyncMock()

    conversation = Conversation(
        id=uuid4(),
        owner_id=uuid4(),
        document_id=uuid4(),
        title="Existing chat",
    )

    repository.get_owned.return_value = conversation

    service = ConversationService(repository, session)

    result = await service.get_or_create(
        conversation_id=conversation.id,
        document_id=conversation.document_id,
        owner_id=conversation.owner_id,
        question="A follow-up question",
    )

    assert result is conversation
    repository.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_different_document():
    repository = AsyncMock()
    session = AsyncMock()

    conversation = Conversation(
        id=uuid4(),
        owner_id=uuid4(),
        document_id=uuid4(),
        title="Existing chat",
    )

    repository.get_owned.return_value = conversation

    service = ConversationService(repository, session)

    with pytest.raises(ConflictException):
        await service.get_or_create(
            conversation_id=conversation.id,
            document_id=uuid4(),
            owner_id=conversation.owner_id,
            question="Question for another document",
        )


@pytest.mark.asyncio
async def test_other_users_conversation_is_not_accessible():
    repository = AsyncMock()
    session = AsyncMock()

    repository.get_owned.return_value = None

    service = ConversationService(repository, session)

    with pytest.raises(NotFoundException):
        await service.get_owned(
            conversation_id=uuid4(),
            owner_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_list_filters_by_owner():
    repository = AsyncMock()
    session = AsyncMock()

    repository.list_owned.return_value = []
    service = ConversationService(repository, session)

    owner_id = uuid4()

    result = await service.list_owned(
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
