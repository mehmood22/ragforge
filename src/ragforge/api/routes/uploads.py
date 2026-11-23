from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.api.auth import CurrentUserDep
from ragforge.core.config import get_settings
from ragforge.core.exceptions import ValidationException
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.models.ingestion_job import JobStatus
from ragforge.schemas.ingestion_job import UploadAcceptedResponse
from ragforge.services.upload_service import UploadService
from ragforge.storage.base import FileStorage
from ragforge.storage.factory import get_storage

router = APIRouter(prefix="/uploads", tags=["Uploads"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
StorageDep = Annotated[FileStorage, Depends(get_storage)]


@router.post(
    "/pdf",
    response_model=ApiResponse[UploadAcceptedResponse],
    status_code=202,
)
async def upload_pdf(
    file: Annotated[UploadFile, File()],
    session: SessionDep,
    storage: StorageDep,
    current_user: CurrentUserDep,
) -> ApiResponse[UploadAcceptedResponse]:
    settings = get_settings()
    filename = (file.filename or "").replace("\\", "/").split("/")[-1]

    if not filename.lower().endswith(".pdf"):
        raise ValidationException("Only PDF files are supported")

    content = await file.read(settings.max_upload_bytes + 1)
    await file.close()

    if len(content) > settings.max_upload_bytes:
        raise ValidationException("PDF exceeds maximum allowed size")

    if not content.startswith(b"%PDF-"):
        raise ValidationException("Invalid PDF signature")

    service = UploadService(session=session, storage=storage)

    result = await service.submit_pdf(
        filename=filename,
        content=content,
        owner_id=current_user.id,
    )

    return success_response(
        data=UploadAcceptedResponse(
            document_id=result.document_id,
            job_id=result.job_id,
            status=JobStatus.PENDING,
        ),
        message="PDF accepted for processing",
    )
