from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.exceptions import DocumentNotFoundException
from ragforge.models.document import (
    Document,
    DocumentStatus,
)
from ragforge.repositories.document_repository import (
    DocumentRepository,
)
from ragforge.schemas.document import DocumentCreate


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        session: AsyncSession,
    ) -> None:
        self.repository = repository
        self.session = session

    async def create_document(
        self,
        payload: DocumentCreate,
    ) -> Document:
        document = Document(
            name=payload.name,
            source_type=payload.source_type.value,
            source_uri=payload.source_uri,
            status=DocumentStatus.PENDING.value,
            chunk_count=0,
        )

        try:
            created = await self.repository.create(document)
            await self.session.commit()
            return created
        except Exception:
            await self.session.rollback()
            raise

    async def get_document(self, document_id: UUID) -> Document:
        document = await self.repository.get_by_id(document_id)

        if document is None:
            raise DocumentNotFoundException()

        return document

    async def list_documents(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        return await self.repository.list_documents(
            limit=limit,
            offset=offset,
        )
