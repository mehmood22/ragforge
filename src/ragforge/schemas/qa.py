from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerStatus(str, Enum):
    ANSWERED = "answered"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class AskRequest(BaseModel):
    document_id: UUID
    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank")
        return value


class GeneratedAnswer(BaseModel):
    status: Literal["answered", "insufficient_context"]
    answer: str
    citations: list[int] = Field(default_factory=list)


class AnswerSource(BaseModel):
    citation: int
    page_number: int
    chunk_index: int
    content: str


class AskResponse(BaseModel):
    answer: str
    status: AnswerStatus
    sources: list[AnswerSource]
