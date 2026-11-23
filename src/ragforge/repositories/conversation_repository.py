from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned(
        self,
        conversation_id: UUID,
        owner_id: UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == owner_id,
        )
        return await self.session.scalar(statement)

    async def list_owned(
        self,
        owner_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(Conversation.owner_id == owner_id)
            .order_by(
                Conversation.updated_at.desc(),
                Conversation.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(statement)
        return list(result.all())

    async def create(
        self,
        conversation: Conversation,
    ) -> Conversation:
        self.session.add(conversation)
        await self.session.flush()
        return conversation
