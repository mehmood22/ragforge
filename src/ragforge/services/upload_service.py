from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.models.document import Document, DocumentStatus
from ragforge.models.ingestion_job import IngestionJob, JobStatus
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

    async def submit_pdf(
        self,
        filename: str,
        content: bytes,
        owner_id: UUID,
    ) -> UploadResult:
        storage_key = f"{uuid4().hex}.pdf"
        stored = await self.storage.upload(storage_key, content)

        try:
            document = Document(
                name=filename,
                source_type="pdf",
                storage_key=stored.key,
                owner_id=owner_id,
                status=DocumentStatus.PENDING.value,
                chunk_count=0,
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
