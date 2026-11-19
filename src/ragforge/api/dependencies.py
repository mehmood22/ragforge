from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.infrastructure.database import get_db_session
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
