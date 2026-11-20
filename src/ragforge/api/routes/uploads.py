from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.schemas.document import DocumentResponse
from ragforge.services.upload_service import UploadService


router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/pdf",
    response_model=ApiResponse[DocumentResponse],
    status_code=201,
)
async def upload_pdf(
    file: Annotated[UploadFile, File()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    upload_service = UploadService(session)
    document = await upload_service.upload_pdf(file)

    return success_response(
        data=document,
        message="PDF indexed successfully",
    )