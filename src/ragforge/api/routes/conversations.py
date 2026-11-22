from typing import Annotated

from fastapi import APIRouter, Depends, Request
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.ai.conversation import (
    build_conversation_graph,
    get_rewrite_model,
)
from ragforge.ai.service import QAService, get_answer_generator
from ragforge.core.config import get_settings
from ragforge.core.exceptions import ConflictException
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.retrieval.service import RetrievalService, get_vector_store
from ragforge.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
)
from ragforge.schemas.qa import AskResponse

router = APIRouter(
    prefix="/conversations",
    tags=["Conversational RAG"],
)

SessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


@router.post(
    "/ask",
    response_model=ApiResponse[ConversationResponse],
)
async def ask_conversation(
    payload: ConversationRequest,
    request: Request,
    session: SessionDep,
) -> ApiResponse[ConversationResponse]:
    settings = get_settings()

    retriever = RetrievalService(
        session=session,
        vector_store=get_vector_store(),
    )

    qa_service = QAService(
        retriever=retriever,
        generator=get_answer_generator(),
        top_k=settings.retrieval_top_k,
        min_score=settings.retrieval_min_score,
        max_context_chars=settings.rag_max_context_chars,
    )

    graph = build_conversation_graph(
        rewrite_model=get_rewrite_model(),
        qa_service=qa_service,
        checkpointer=request.app.state.checkpointer,
    )

    thread_id = f"{payload.document_id}:{payload.conversation_id}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    previous = await graph.aget_state(config)

    if previous.values:
        previous_document_id = previous.values.get("document_id")

        if previous_document_id != str(payload.document_id):
            raise ConflictException("Conversation belongs to another document")

    state = await graph.ainvoke(
        {
            "document_id": str(payload.document_id),
            "messages": [
                HumanMessage(content=payload.question),
            ],
        },
        config=config,
    )

    result = AskResponse.model_validate(state["result"])

    return success_response(
        data=ConversationResponse(
            conversation_id=payload.conversation_id,
            document_id=payload.document_id,
            standalone_question=state["standalone_question"],
            result=result,
        ),
        message="Conversation question processed successfully",
    )
