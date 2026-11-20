from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import Settings, get_settings
from ragforge.core.responses import ApiResponse, success_response
from ragforge.infrastructure.database import get_db_session
from ragforge.schemas.document import DocumentResponse
from ragforge.services.upload_service import UploadService
from ragforge.storage.base import FileStorage
from ragforge.storage.factory import get_storage

router = APIRouter(prefix="/uploads", tags=["Uploads"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
StorageDep = Annotated[FileStorage, Depends(get_storage)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_upload_service(
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
) -> UploadService:
    return UploadService(
        session=session,
        storage=storage,
        settings=settings,
    )


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
