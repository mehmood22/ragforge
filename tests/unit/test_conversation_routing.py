from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from ragforge.ai.conversation import build_conversation_graph
from ragforge.schemas.qa import AnswerStatus, AskResponse


@pytest.mark.asyncio
async def test_no_context_skips_generation() -> None:
    retriever = AsyncMock()
    retriever.search.return_value = []

    qa_service = AsyncMock()
    qa_service.retriever = retriever
    qa_service.top_k = 5
    qa_service.min_score = 0.35
    qa_service._insufficient = MagicMock(
        return_value=AskResponse(
            answer="The provided documents do not contain enough information to answer this question.",
            status=AnswerStatus.INSUFFICIENT_CONTEXT,
            sources=[],
        )
    )

    rewrite_model = AsyncMock()

    graph = build_conversation_graph(
        rewrite_model=rewrite_model,
        qa_service=qa_service,
        checkpointer=MemorySaver(),
    )

    result = await graph.ainvoke(
        {
            "document_id": str(uuid4()),
            "messages": [HumanMessage(content="What is the annual revenue?")],
        },
        config={
            "configurable": {
                "thread_id": str(uuid4()),
            }
        },
    )

    assert result["result"]["status"] == "insufficient_context"
    qa_service.answer_from_chunks.assert_not_awaited()
    rewrite_model.ainvoke.assert_not_awaited()
