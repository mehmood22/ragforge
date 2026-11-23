from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.models.document import Document, DocumentStatus
from ragforge.models.ingestion_job import IngestionJob, JobStatus


class IngestionJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, document_id: UUID) -> IngestionJob:
        job = IngestionJob(
            document_id=document_id,
            status=JobStatus.PENDING.value,
            attempts=0,
            max_attempts=3,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: UUID) -> IngestionJob | None:
        return await self.session.get(IngestionJob, job_id)

    async def claim_next(self, lease_seconds: int = 900) -> IngestionJob | None:
        now = datetime.now(UTC)

        statement = (
            select(IngestionJob)
            .where(
                or_(
                    (
                        (IngestionJob.status == JobStatus.PENDING.value)
                        & (
                            (IngestionJob.available_at.is_(None))
                            | (IngestionJob.available_at <= now)
                        )
                    ),
                    (
                        (IngestionJob.status == JobStatus.PROCESSING.value)
                        & (IngestionJob.locked_until < now)
                    ),
                ),
                IngestionJob.attempts < IngestionJob.max_attempts,
            )
            .order_by(IngestionJob.created_at, IngestionJob.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )

        result = await self.session.execute(statement)
        job = result.scalar_one_or_none()

        if job is None:
            return None

        job.status = JobStatus.PROCESSING.value
        job.attempts += 1
        job.lease_token = uuid4()
        job.locked_until = now + timedelta(seconds=lease_seconds)
        job.available_at = None

        await self.session.flush()
        return job

    async def finish(
        self,
        job_id: UUID,
        lease_token: UUID,
        status: JobStatus,
        error_code: str | None = None,
        retry_at: datetime | None = None,
    ) -> bool:
        statement = (
            update(IngestionJob)
            .where(
                IngestionJob.id == job_id,
                IngestionJob.lease_token == lease_token,
                IngestionJob.status == JobStatus.PROCESSING.value,
            )
            .values(
                status=status.value,
                locked_until=None,
                lease_token=None,
                available_at=retry_at,
                last_error=error_code,
                updated_at=datetime.now(UTC),
            )
        )

        result = await self.session.execute(statement)
        cursor_result = cast(CursorResult[Any], result)
        return cursor_result.rowcount == 1

    async def fail_exhausted_leases(self) -> int:
        now = datetime.now(UTC)

        statement = (
            select(IngestionJob)
            .where(
                IngestionJob.status == JobStatus.PROCESSING.value,
                IngestionJob.locked_until < now,
                IngestionJob.attempts >= IngestionJob.max_attempts,
            )
            .with_for_update(skip_locked=True)
            .limit(100)
        )

        jobs = (await self.session.scalars(statement)).all()

        for job in jobs:
            job.status = JobStatus.FAILED.value
            job.lease_token = None
            job.locked_until = None
            job.last_error = "LEASE_EXHAUSTED"

            document = await self.session.get(Document, job.document_id)

            if document is not None:
                document.status = DocumentStatus.FAILED.value

        return len(jobs)

    async def get_owned(
        self,
        job_id: UUID,
        owner_id: UUID,
    ) -> IngestionJob | None:
        statement = (
            select(IngestionJob)
            .join(
                Document,
                IngestionJob.document_id == Document.id,
            )
            .where(
                IngestionJob.id == job_id,
                Document.owner_id == owner_id,
            )
        )

        return await self.session.scalar(statement)
