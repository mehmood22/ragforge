from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from ragforge.core.responses import ApiResponse, success_response
from ragforge.schemas.document import DocumentResponse
from ragforge.services.upload_service import UploadService, get_upload_service

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


@router.post(
    "/pdf",
    response_model=ApiResponse[DocumentResponse],
    status_code=201,
)
async def upload_pdf(
    file: Annotated[UploadFile, File()],
    upload_service: UploadServiceDep,
) -> ApiResponse[DocumentResponse]:
    document = await upload_service.upload_and_ingest_pdf(file)
    return success_response(
        data=document,
        message="PDF indexed successfully",
    )
