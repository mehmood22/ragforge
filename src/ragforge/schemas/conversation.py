from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ragforge.schemas.qa import AskResponse


class ConversationRequest(BaseModel):
    document_id: UUID
    conversation_id: UUID
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank")
        return value


class ConversationResponse(BaseModel):
    conversation_id: UUID
    document_id: UUID
    standalone_question: str
    result: AskResponse
