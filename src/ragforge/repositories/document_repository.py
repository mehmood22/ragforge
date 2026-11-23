from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)

        # Flush to assign DB defaults/IDs in the current transaction; let the service layer commit.
        await self.session.flush()
        await self.session.refresh(document)

        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list_documents(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        statement = (
            select(Document)
            .order_by(Document.created_at.desc(), Document.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(statement)

        return list(result.all())

    async def get_owned(
        self,
        document_id: UUID,
        owner_id: UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )

        return await self.session.scalar(statement)

    async def list_owned(
        self,
        owner_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(
                Document.created_at.desc(),
                Document.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(statement)

        return list(result.all())
