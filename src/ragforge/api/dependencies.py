from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.infrastructure.database import get_db_session
from ragforge.models.document import Document
from ragforge.repositories.document_repository import (
    DocumentRepository,
)
from ragforge.services.document_service import DocumentService


async def get_document_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentService:
    repository = DocumentRepository(session)

    return DocumentService(
        repository=repository,
        session=session,
    )


async def require_owned_document(
    session: AsyncSession,
    document_id: UUID,
    owner_id: UUID,
) -> Document:
    repository = DocumentRepository(session)

    document = await repository.get_owned(
        document_id=document_id,
        owner_id=owner_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document
