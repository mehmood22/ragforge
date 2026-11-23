from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.ai.service import (
    QAService,
    get_answer_generator,
)
from ragforge.api.auth import CurrentUserDep
from ragforge.api.dependencies import require_owned_document
from ragforge.core.config import get_settings
from ragforge.core.responses import (
    ApiResponse,
    success_response,
)
from ragforge.infrastructure.database import get_db_session
from ragforge.retrieval.service import (
    RetrievalService,
    get_vector_store,
)
from ragforge.schemas.qa import AskRequest, AskResponse

router = APIRouter(prefix="/qa", tags=["AI Question Answering (Not Conversation Q&A)"])

SessionDep = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


@router.post(
    "/ask",
    response_model=ApiResponse[AskResponse],
)
async def ask_question(
    payload: AskRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ApiResponse[AskResponse]:
    await require_owned_document(
        session=session,
        document_id=payload.document_id,
        owner_id=current_user.id,
    )

    settings = get_settings()

    retriever = RetrievalService(
        session=session,
        vector_store=get_vector_store(),
    )

    service = QAService(
        retriever=retriever,
        generator=get_answer_generator(),
        top_k=settings.retrieval_top_k,
        min_score=settings.retrieval_min_score,
        max_context_chars=settings.rag_max_context_chars,
    )

    result = await service.ask(
        document_id=payload.document_id,
        question=payload.question,
    )

    return success_response(
        data=result,
        message="Question processed successfully",
    )
