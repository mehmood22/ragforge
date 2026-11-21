import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from ragforge.core.config import get_settings
from ragforge.core.logging import configure_logging
from ragforge.infrastructure.database import SessionFactory
from ragforge.ingestion.processor import PDFProcessor
from ragforge.models.document import Document, DocumentStatus
from ragforge.models.ingestion_job import IngestionJob, JobStatus
from ragforge.repositories.ingestion_job_repository import (
    IngestionJobRepository,
)
from ragforge.storage.factory import get_storage

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 3
LEASE_SECONDS = 900


async def claim_job() -> tuple[UUID, UUID, UUID] | None:
    async with SessionFactory.begin() as session:
        repository = IngestionJobRepository(session)
        job = await repository.claim_next(LEASE_SECONDS)

        if job is None:
            return None

        if job.lease_token is None:
            raise RuntimeError("Claimed job is missing a lease token")

        document = await session.get(Document, job.document_id)

        if document is None:
            raise RuntimeError("Job references a missing document")

        document.status = DocumentStatus.PROCESSING.value

        return job.id, job.document_id, job.lease_token


async def complete_job(
    job_id: UUID,
    document_id: UUID,
    token: UUID,
    chunk_count: int,
) -> bool:
    async with SessionFactory.begin() as session:
        repository = IngestionJobRepository(session)

        job = await session.scalar(
            select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
        )

        now = datetime.now(UTC)

        if (
            job is None
            or job.lease_token != token
            or job.status != JobStatus.PROCESSING.value
            or job.locked_until is None
            or job.locked_until <= now
        ):
            return False

        document = await session.get(Document, document_id)

        if document is None:
            return False

        finished = await repository.finish(
            job_id=job_id,
            lease_token=token,
            status=JobStatus.COMPLETED,
        )

        if not finished:
            return False

        document.status = DocumentStatus.INDEXED.value
        document.chunk_count = chunk_count
        document.indexed_generation = token

        return True


async def fail_job(
    job_id: UUID,
    document_id: UUID,
    token: UUID,
    retryable: bool,
    error_code: str,
) -> None:
    async with SessionFactory.begin() as session:
        repository = IngestionJobRepository(session)

        job = await session.scalar(
            select(IngestionJob).where(IngestionJob.id == job_id).with_for_update()
        )

        now = datetime.now(UTC)

        if (
            job is None
            or job.lease_token != token
            or job.status != JobStatus.PROCESSING.value
            or job.locked_until is None
            or job.locked_until <= now
        ):
            return

        should_retry = retryable and job.attempts < job.max_attempts

        retry_at = (
            now + timedelta(seconds=min(60 * (2 ** (job.attempts - 1)), 600))
            if should_retry
            else None
        )

        new_status = JobStatus.PENDING if should_retry else JobStatus.FAILED

        finished = await repository.finish(
            job_id=job_id,
            lease_token=token,
            status=new_status,
            error_code=error_code,
            retry_at=retry_at,
        )

        if not finished:
            return

        document = await session.get(Document, document_id)

        if document is not None:
            document.status = (
                DocumentStatus.PENDING.value
                if should_retry
                else DocumentStatus.FAILED.value
            )


async def process_job(
    job_id: UUID,
    document_id: UUID,
    token: UUID,
) -> None:
    async with SessionFactory() as session:
        document = await session.get(Document, document_id)

        if document is None or not document.storage_key:
            await fail_job(
                job_id,
                document_id,
                token,
                retryable=False,
                error_code="MISSING_SOURCE",
            )
            return

        storage_key = document.storage_key

    processor = PDFProcessor(
        storage=get_storage(),
        settings=get_settings(),
    )

    try:
        chunk_count = await asyncio.wait_for(
            processor.process(
                document_id=document_id,
                generation_id=token,
                storage_key=storage_key,
            ),
            timeout=LEASE_SECONDS - 30,
        )

        completed = await complete_job(
            job_id,
            document_id,
            token,
            chunk_count,
        )

        if not completed:
            logger.warning(
                "Job completion rejected: lease lost",
                extra={"job_id": str(job_id)},
            )

    except (ValueError, FileNotFoundError):
        logger.warning(
            "Document cannot be processed",
            extra={"job_id": str(job_id)},
        )
        await fail_job(
            job_id,
            document_id,
            token,
            retryable=False,
            error_code="INVALID_SOURCE",
        )

    except Exception:
        logger.exception(
            "Ingestion attempt failed",
            extra={"job_id": str(job_id)},
        )
        await fail_job(
            job_id,
            document_id,
            token,
            retryable=True,
            error_code="PROCESSING_ERROR",
        )


async def run_worker() -> None:
    while True:
        try:
            await recover_exhausted_jobs()

            claimed = await claim_job()

            if claimed is None:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            await process_job(*claimed)

        except Exception:
            logger.exception("Worker iteration failed")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def recover_exhausted_jobs() -> None:
    async with SessionFactory.begin() as session:
        repository = IngestionJobRepository(session)
        recovered = await repository.fail_exhausted_leases()

        if recovered:
            logger.warning(
                "Exhausted jobs marked failed",
                extra={"recovered_count": recovered},
            )


def main() -> None:
    configure_logging(get_settings().log_level)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
