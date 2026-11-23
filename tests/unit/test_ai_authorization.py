from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from ragforge.api.dependencies import require_owned_document
from ragforge.api.routes.conversations import ask_conversation
from ragforge.api.routes.qa import ask_question
from ragforge.api.routes.retrieval import search_documents
from ragforge.schemas.conversation import ConversationRequest
from ragforge.schemas.qa import AskRequest
from ragforge.schemas.retrieval import RetrievalRequest


@asynccontextmanager
async def fake_conversation_lock(conversation_id):
    yield


@pytest.mark.asyncio
async def test_retrieval_rejects_other_users_document():
    document_id = uuid4()
    owner_id = uuid4()

    session = AsyncMock()

    current_user = type(
        "User",
        (),
        {"id": owner_id},
    )()

    with (
        patch(
            "ragforge.api.routes.retrieval.require_owned_document",
            new_callable=AsyncMock,
        ) as authorize,
        patch(
            "ragforge.api.routes.retrieval.get_vector_store",
        ) as vector_store,
    ):
        authorize.side_effect = HTTPException(
            status_code=404,
            detail="Document not found",
        )

        with pytest.raises(HTTPException) as exc:
            await search_documents(
                payload=RetrievalRequest(
                    document_id=document_id,
                    query="What is the policy?",
                ),
                session=session,
                current_user=current_user,
            )

        assert exc.value.status_code == 404
        vector_store.assert_not_called()


@pytest.mark.asyncio
async def test_qa_rejects_other_users_document():
    document_id = uuid4()
    session = AsyncMock()
    current_user = type("User", (), {"id": uuid4()})()

    with (
        patch(
            "ragforge.api.routes.qa.require_owned_document",
            new_callable=AsyncMock,
        ) as authorize,
        patch(
            "ragforge.api.routes.qa.get_answer_generator",
        ) as generator,
    ):
        authorize.side_effect = HTTPException(
            status_code=404,
            detail="Document not found",
        )

        with pytest.raises(HTTPException) as exc:
            await ask_question(
                payload=AskRequest(
                    document_id=document_id,
                    question="What is the policy?",
                ),
                session=session,
                current_user=current_user,
            )

        assert exc.value.status_code == 404
        generator.assert_not_called()


@pytest.mark.asyncio
async def test_conversation_rejects_other_users_document():
    document_id = uuid4()
    session = AsyncMock()
    current_user = type("User", (), {"id": uuid4()})()

    request = type("Request", (), {})()

    with (
        patch(
            "ragforge.api.routes.conversations.conversation_lock",
            fake_conversation_lock,
        ),
        patch(
            "ragforge.api.routes.conversations.require_owned_document",
            new_callable=AsyncMock,
        ) as authorize,
        patch(
            "ragforge.api.routes.conversations.build_conversation_graph",
        ) as graph_builder,
    ):
        authorize.side_effect = HTTPException(
            status_code=404,
            detail="Document not found",
        )

        with pytest.raises(HTTPException) as exc:
            await ask_conversation(
                payload=ConversationRequest(
                    document_id=document_id,
                    conversation_id=uuid4(),
                    question="What about Germany?",
                ),
                request=request,
                session=session,
                current_user=current_user,
            )

        assert exc.value.status_code == 404
        graph_builder.assert_not_called()


@pytest.mark.asyncio
async def test_ownership_helper_rejects_missing_document():
    session = AsyncMock()
    document_id = uuid4()
    owner_id = uuid4()

    with patch("ragforge.api.dependencies.DocumentRepository") as repository_class:
        repository = repository_class.return_value
        repository.get_owned = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await require_owned_document(
                session=session,
                document_id=document_id,
                owner_id=owner_id,
            )

        assert exc.value.status_code == 404

        repository.get_owned.assert_awaited_once_with(
            document_id=document_id,
            owner_id=owner_id,
        )
