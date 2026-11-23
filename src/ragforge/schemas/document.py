from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ragforge.models.document import (
    DocumentStatus,
    SourceType,
)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: SourceType
    source_uri: str | None
    status: DocumentStatus
    chunk_count: int
    storage_key: str | None
    created_at: datetime
    updated_at: datetime
