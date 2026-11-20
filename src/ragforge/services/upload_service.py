from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import Settings
from ragforge.core.exceptions import ValidationException
from ragforge.models.document import SourceType
from ragforge.repositories.document_repository import DocumentRepository
from ragforge.schemas.document import DocumentCreate, DocumentResponse
from ragforge.services.document_service import DocumentService
from ragforge.services.ingestion_service import IngestionService
from ragforge.storage.base import FileStorage
from ragforge.storage.helpers import delete_file_safely


class UploadService:
    def __init__(
        self,
        session: AsyncSession,
        storage: FileStorage,
        settings: Settings,
    ) -> None:
        self.session = session
        self.storage = storage
        self.settings = settings
        self.document_service = DocumentService(
            DocumentRepository(session),
            session,
        )
        self.ingestion_service = IngestionService(
            session=session,
            storage=storage,
        )

    async def upload_and_ingest_pdf(self, file: UploadFile) -> DocumentResponse:
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise ValidationException("Only PDF files are supported")

        content = await file.read(self.settings.max_upload_bytes + 1)
        await file.close()

        if len(content) > self.settings.max_upload_bytes:
            raise ValidationException("PDF exceeds maximum allowed size")

        if not content.startswith(b"%PDF-"):
            raise ValidationException("Invalid PDF signature")

        storage_key = f"{uuid4().hex}.pdf"
        stored = await self.storage.upload(storage_key, content)

        try:
            document = await self.document_service.create_document(
                DocumentCreate(
                    name=filename.replace("\\", "/").split("/")[-1],
                    source_type=SourceType.PDF,
                    source_uri=None,
                    storage_key=stored.key,
                )
            )

            await self.ingestion_service.ingest_pdf(
                document_id=document.id,
                storage_key=stored.key,
            )

            await self.session.refresh(document)
            return DocumentResponse.model_validate(document)

        except Exception:
            await delete_file_safely(self.storage, stored.key)
            raise
