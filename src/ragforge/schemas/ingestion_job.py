from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ragforge.models.ingestion_job import JobStatus


class UploadAcceptedResponse(BaseModel):
    document_id: UUID
    job_id: UUID
    status: JobStatus


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    status: JobStatus
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
