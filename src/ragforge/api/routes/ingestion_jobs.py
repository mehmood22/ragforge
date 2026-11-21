from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.exceptions import NotFoundException
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.repositories.ingestion_job_repository import (
    IngestionJobRepository,
)
from ragforge.schemas.ingestion_job import IngestionJobResponse

router = APIRouter(
    prefix="/ingestion-jobs",
    tags=["Ingestion Jobs"],
)


@router.get(
    "/{job_id}",
    response_model=ApiResponse[IngestionJobResponse],
)
async def get_ingestion_job(
    job_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IngestionJobResponse]:
    repository = IngestionJobRepository(session)
    job = await repository.get_by_id(job_id)

    if job is None:
        raise NotFoundException("Ingestion job not found")

    return success_response(
        data=IngestionJobResponse.model_validate(job),
        message="Ingestion job retrieved successfully",
    )
