from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import get_settings
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.retrieval.service import (
    RetrievalService,
    get_vector_store,
)
from ragforge.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
)

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)


@router.post(
    "/search",
    response_model=ApiResponse[RetrievalResponse],
)
async def search_documents(
    payload: RetrievalRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[RetrievalResponse]:
    settings = get_settings()

    service = RetrievalService(
        session=session,
        vector_store=get_vector_store(),
    )

    chunks = await service.search(
        document_id=payload.document_id,
        query=payload.query.strip(),
        top_k=payload.top_k or settings.retrieval_top_k,
        min_score=settings.retrieval_min_score,
    )

    response = RetrievalResponse(
        query=payload.query.strip(),
        document_id=payload.document_id,
        results=chunks,
        total=len(chunks),
    )

    return success_response(
        data=response,
        message="Retrieval completed successfully",
    )
