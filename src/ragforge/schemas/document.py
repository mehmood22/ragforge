from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ragforge.models.document import (
    DocumentStatus,
    SourceType,
)


class DocumentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    source_uri: str | None = Field(
        default=None,
        max_length=2048,
    )


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: SourceType
    source_uri: str | None
    status: DocumentStatus
    chunk_count: int
    created_at: datetime
    updated_at: datetime
