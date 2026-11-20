from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import get_settings
from ragforge.core.exceptions import ValidationException
from ragforge.infrastructure.storage import LocalFileStorage
from ragforge.models.document import SourceType
from ragforge.repositories.document_repository import DocumentRepository
from ragforge.schemas.document import DocumentCreate, DocumentResponse
from ragforge.services.document_service import DocumentService
from ragforge.services.ingestion_service import IngestionService


class UploadService:
    def __init__(
        self,
        session: AsyncSession,
        storage: LocalFileStorage | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.storage = storage or LocalFileStorage(self.settings.upload_directory)

    async def upload_pdf(self, file: UploadFile) -> DocumentResponse:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise ValidationException("Only PDF files are supported")

        content = await file.read(self.settings.max_upload_bytes + 1)
        await file.close()

        if len(content) > self.settings.max_upload_bytes:
            raise ValidationException("PDF exceeds maximum allowed size")

        if not content.startswith(b"%PDF-"):
            raise ValidationException("Invalid PDF file signature")

        # Never use the supplied filename as a filesystem path.
        stored_path = await self.storage.save_bytes(content, extension=".pdf")

        repository = DocumentRepository(self.session)
        document_service = DocumentService(repository, self.session)

        try:
            document = await document_service.create_document(
                DocumentCreate(
                    name=Path(file.filename.replace("\\", "/")).name,
                    source_type=SourceType.PDF,
                )
            )

            ingestion_service = IngestionService(self.session)
            await ingestion_service.ingest_pdf(document.id, stored_path)

            await self.session.refresh(document)

            return DocumentResponse.model_validate(document)

        except Exception:
            await self.storage.delete_file(stored_path)
            raise