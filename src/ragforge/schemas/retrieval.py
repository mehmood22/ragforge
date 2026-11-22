from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    document_id: UUID
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RetrievedChunk(BaseModel):
    content: str
    document_id: UUID
    page_number: int
    chunk_index: int
    score: float


class RetrievalResponse(BaseModel):
    query: str
    document_id: UUID
    results: list[RetrievedChunk]
    total: int
