from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.exceptions import DocumentNotFoundException
from ragforge.models.document import (
    Document,
)
from ragforge.repositories.document_repository import (
    DocumentRepository,
)


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        session: AsyncSession,
    ) -> None:
        self.repository = repository
        self.session = session

    async def get_document(
        self,
        document_id: UUID,
        owner_id: UUID,
    ) -> Document:
        document = await self.repository.get_owned(
            document_id=document_id,
            owner_id=owner_id,
        )

        if document is None:
            raise DocumentNotFoundException()

        return document

    async def list_documents(
        self,
        owner_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        return await self.repository.list_owned(
            owner_id=owner_id,
            limit=limit,
            offset=offset,
        )
