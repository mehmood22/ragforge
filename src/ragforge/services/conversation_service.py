from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from ragforge.models.conversation import Conversation
from ragforge.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        session: AsyncSession,
    ) -> None:
        self.repository = repository
        self.session = session

    async def get_owned(
        self,
        conversation_id: UUID,
        owner_id: UUID,
    ) -> Conversation:
        conversation = await self.repository.get_owned(
            conversation_id=conversation_id,
            owner_id=owner_id,
        )

        if conversation is None:
            raise NotFoundException("Conversation not found")

        return conversation

    async def get_or_create(
        self,
        conversation_id: UUID,
        document_id: UUID,
        owner_id: UUID,
        question: str,
    ) -> Conversation:
        conversation = await self.repository.get_owned(
            conversation_id=conversation_id,
            owner_id=owner_id,
        )

        if conversation is not None:
            if conversation.document_id != document_id:
                raise ConflictException("Conversation belongs to another document")

            return conversation

        # A UUID already used by another account must not be reused.
        existing = await self.session.get(
            Conversation,
            conversation_id,
        )

        if existing is not None:
            raise NotFoundException("Conversation not found")

        conversation = Conversation(
            id=conversation_id,
            owner_id=owner_id,
            document_id=document_id,
            title=question[:200],
        )

        await self.repository.create(conversation)
        await self.session.commit()

        return conversation

    async def touch(self, conversation: Conversation) -> None:
        conversation.updated_at = datetime.now(UTC)
        await self.session.commit()

    async def list_owned(
        self,
        owner_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        return await self.repository.list_owned(
            owner_id=owner_id,
            limit=limit,
            offset=offset,
        )
