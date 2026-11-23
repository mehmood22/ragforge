from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.ai.conversation import (
    build_conversation_graph,
    get_rewrite_model,
)
from ragforge.ai.service import QAService, get_answer_generator
from ragforge.api.auth import CurrentUserDep
from ragforge.api.dependencies import require_owned_document
from ragforge.core.config import get_settings
from ragforge.core.exceptions import ConflictException
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.conversation_lock import (
    conversation_lock,
)
from ragforge.infrastructure.database import get_db_session
from ragforge.repositories.conversation_repository import ConversationRepository
from ragforge.retrieval.service import RetrievalService, get_vector_store
from ragforge.schemas.conversation import (
    ConversationHistoryResponse,
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
    ConversationSummary,
)
from ragforge.schemas.qa import AskResponse
from ragforge.services.conversation_service import ConversationService
from ragforge.services.conversation_threads import (
    conversation_thread_id,
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversational RAG"],
)

SessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def get_conversation_service(
    session: SessionDep,
) -> ConversationService:
    return ConversationService(
        repository=ConversationRepository(session),
        session=session,
    )


@router.post(
    "/ask",
    response_model=ApiResponse[ConversationResponse],
)
async def ask_conversation(
    payload: ConversationRequest,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ApiResponse[ConversationResponse]:
    # 1. Verify document ownership.
    await require_owned_document(
        session=session,
        document_id=payload.document_id,
        owner_id=current_user.id,
    )

    # 2. Lock this conversation across all API instances.
    async with conversation_lock(payload.conversation_id):
        conversation_service = get_conversation_service(session)

        # 3. Create or validate conversation metadata.
        conversation = await conversation_service.get_or_create(
            conversation_id=payload.conversation_id,
            document_id=payload.document_id,
            owner_id=current_user.id,
            question=payload.question,
        )

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

        thread_id = conversation_thread_id(
            owner_id=current_user.id,
            document_id=payload.document_id,
            conversation_id=payload.conversation_id,
        )

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # 4. Read the latest checkpoint while locked.
        previous = await graph.aget_state(config)

        if previous.values:
            previous_document_id = previous.values.get("document_id")

            if previous_document_id != str(payload.document_id):
                raise ConflictException("Conversation belongs to another document")

        # 5. Execute the graph while holding the lock.
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

        # 6. Update the last-activity timestamp.
        await conversation_service.touch(conversation)

        return success_response(
            data=ConversationResponse(
                conversation_id=payload.conversation_id,
                document_id=payload.document_id,
                standalone_question=state["standalone_question"],
                result=result,
            ),
            message="Conversation question processed successfully",
        )


@router.get(
    "",
    response_model=ApiResponse[list[ConversationSummary]],
)
async def list_conversations(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[ConversationSummary]]:
    service = get_conversation_service(session)

    conversations = await service.list_owned(
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return success_response(
        data=[ConversationSummary.model_validate(item) for item in conversations],
        message="Conversations retrieved successfully",
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=ApiResponse[ConversationHistoryResponse],
)
async def get_conversation_messages(
    conversation_id: UUID,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ApiResponse[ConversationHistoryResponse]:
    service = get_conversation_service(session)

    # 1. Verify that the conversation belongs to this user.
    conversation = await service.get_owned(
        conversation_id=conversation_id,
        owner_id=current_user.id,
    )

    # 2. Verify the associated document still belongs
    #    to this user.
    await require_owned_document(
        session=session,
        document_id=conversation.document_id,
        owner_id=current_user.id,
    )

    # 3. Construct exactly the same LangGraph thread ID
    #    used by the /ask endpoint.
    thread_id = conversation_thread_id(
        owner_id=current_user.id,
        document_id=conversation.document_id,
        conversation_id=conversation.id,
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # 4. Load the latest checkpoint directly.
    #    No Groq or ChromaDB call is required.
    checkpoint = await request.app.state.checkpointer.aget(config)

    messages: list[ConversationMessage] = []

    if checkpoint is not None:
        values = checkpoint.get("channel_values", {})

        # Defense in depth: ensure checkpoint data is
        # associated with the same document.
        if values.get("document_id") != str(conversation.document_id):
            raise ConflictException("Conversation checkpoint document mismatch")

        for message in values.get("messages", []):
            if not isinstance(message.content, str):
                continue

            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue

            messages.append(
                ConversationMessage(
                    role=role,
                    content=message.content,
                )
            )

    response = ConversationHistoryResponse(
        conversation_id=conversation.id,
        document_id=conversation.document_id,
        title=conversation.title,
        messages=messages,
    )

    return success_response(
        data=response,
        message="Conversation history retrieved successfully",
    )
