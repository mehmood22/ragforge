from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from ragforge.ai.conversation import build_conversation_graph
from ragforge.schemas.qa import (
    AnswerStatus,
    AskResponse,
)


@pytest.mark.asyncio
async def test_conversation_remembers_previous_turns() -> None:
    document_id = uuid4()
    conversation_id = uuid4()

    rewrite_model = AsyncMock()
    rewrite_model.ainvoke.return_value = AIMessage(
        content="Does the roaming policy apply in Germany?"
    )

    qa_service = AsyncMock()
    qa_service.ask.return_value = AskResponse(
        answer="The document does not specify Germany.",
        status=AnswerStatus.INSUFFICIENT_CONTEXT,
        sources=[],
    )

    graph = build_conversation_graph(
        rewrite_model=rewrite_model,
        qa_service=qa_service,
        checkpointer=MemorySaver(),
    )

    config = {
        "configurable": {
            "thread_id": f"{document_id}:{conversation_id}",
        }
    }

    first = await graph.ainvoke(
        {
            "document_id": str(document_id),
            "messages": [
                HumanMessage(content="What is the international roaming policy?")
            ],
        },
        config=config,
    )

    assert len(first["messages"]) == 2
    rewrite_model.ainvoke.assert_not_awaited()

    second = await graph.ainvoke(
        {
            "document_id": str(document_id),
            "messages": [HumanMessage(content="Does it apply in Germany?")],
        },
        config=config,
    )

    assert len(second["messages"]) == 4

    assert second["standalone_question"] == (
        "Does the roaming policy apply in Germany?"
    )

    qa_service.ask.assert_any_await(
        document_id=document_id,
        question="Does the roaming policy apply in Germany?",
    )

    rewrite_model.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_different_conversations_are_isolated() -> None:
    document_id = uuid4()

    rewrite_model = AsyncMock()
    qa_service = AsyncMock()

    qa_service.ask.return_value = AskResponse(
        answer="Not enough information.",
        status=AnswerStatus.INSUFFICIENT_CONTEXT,
        sources=[],
    )

    graph = build_conversation_graph(
        rewrite_model=rewrite_model,
        qa_service=qa_service,
        checkpointer=MemorySaver(),
    )

    for conversation_id in (uuid4(), uuid4()):
        result = await graph.ainvoke(
            {
                "document_id": str(document_id),
                "messages": [HumanMessage(content="What is the policy?")],
            },
            config={"configurable": {"thread_id": f"{document_id}:{conversation_id}"}},
        )

        assert len(result["messages"]) == 2

    rewrite_model.ainvoke.assert_not_awaited()
