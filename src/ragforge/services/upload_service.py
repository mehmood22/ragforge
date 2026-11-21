from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.models.document import Document, DocumentStatus
from ragforge.models.ingestion_job import IngestionJob, JobStatus
from ragforge.repositories.document_repository import DocumentRepository
from ragforge.services.document_service import DocumentService
from ragforge.services.ingestion_service import IngestionService
from ragforge.storage.base import FileStorage


@dataclass(frozen=True)
class UploadResult:
    document_id: UUID
    job_id: UUID


class UploadService:
    def __init__(
        self,
        session: AsyncSession,
        storage: FileStorage,
    ) -> None:
        self.session = session
        self.storage = storage
        self.document_service = DocumentService(
            DocumentRepository(session),
            session,
        )
        self.ingestion_service = IngestionService(
            session=session,
            storage=storage,
        )

    async def submit_pdf(
        self,
        filename: str,
        content: bytes,
    ) -> UploadResult:
        storage_key = f"{uuid4().hex}.pdf"

        stored = await self.storage.upload(storage_key, content)

        try:
            document = Document(
                name=filename,
                source_type="pdf",
                storage_key=stored.key,
                status=DocumentStatus.PENDING.value,
                chunk_count=0,
            )

            job = IngestionJob(
                document_id=document.id,
                status=JobStatus.PENDING.value,
                attempts=0,
                max_attempts=3,
            )

            self.session.add(document)
            await self.session.flush()

            job = IngestionJob(
                document_id=document.id,
                status=JobStatus.PENDING.value,
                attempts=0,
                max_attempts=3,
            )

            self.session.add(job)
            await self.session.flush()
            await self.session.commit()

            return UploadResult(
                document_id=document.id,
                job_id=job.id,
            )

        except Exception:
            await self.session.rollback()
            await self.storage.delete(stored.key)
            raise
