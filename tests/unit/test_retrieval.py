from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from langchain_core.documents import Document as LangChainDocument

from ragforge.core.exceptions import (
    ConflictException,
    DocumentNotFoundException,
)
from ragforge.retrieval.service import RetrievalService


@pytest.mark.asyncio
async def test_retrieval_returns_relevant_chunks() -> None:
    document_id = uuid4()
    generation_id = uuid4()

    session = AsyncMock()
    session.get.return_value = SimpleNamespace(
        status="indexed",
        indexed_generation=generation_id,
    )

    vector_store = Mock()
    vector_store.similarity_search_with_relevance_scores.return_value = [
        (
            LangChainDocument(
                page_content="Roaming charges depend on the plan.",
                metadata={
                    "document_id": str(document_id),
                    "generation_id": str(generation_id),
                    "page_number": 3,
                    "chunk_index": 7,
                },
            ),
            0.85,
        )
    ]

    service = RetrievalService(session, vector_store)

    results = await service.search(
        document_id=document_id,
        query="What are roaming charges?",
        top_k=5,
        min_score=0.35,
    )

    assert len(results) == 1
    assert results[0].page_number == 3
    assert results[0].chunk_index == 7
    assert results[0].score == 0.85

    vector_store.similarity_search_with_relevance_scores.assert_called_once_with(
        "What are roaming charges?",
        k=5,
        filter={
            "$and": [
                {"document_id": str(document_id)},
                {"generation_id": str(generation_id)},
            ]
        },
        score_threshold=0.35,
    )


@pytest.mark.asyncio
async def test_retrieval_rejects_missing_document() -> None:
    session = AsyncMock()
    session.get.return_value = None

    vector_store = Mock()
    service = RetrievalService(session, vector_store)

    with pytest.raises(DocumentNotFoundException):
        await service.search(
            document_id=uuid4(),
            query="Test question",
            top_k=5,
            min_score=0.35,
        )

    vector_store.similarity_search_with_relevance_scores.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_rejects_unindexed_document() -> None:
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(
        status="pending",
        indexed_generation=None,
    )

    vector_store = Mock()
    service = RetrievalService(session, vector_store)

    with pytest.raises(ConflictException):
        await service.search(
            document_id=uuid4(),
            query="Test question",
            top_k=5,
            min_score=0.35,
        )

    vector_store.similarity_search_with_relevance_scores.assert_not_called()
