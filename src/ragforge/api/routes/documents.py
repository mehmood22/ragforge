from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ragforge.api.dependencies import get_document_service
from ragforge.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from ragforge.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ServiceDep = Annotated[
    DocumentService,
    Depends(get_document_service),
]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    service: ServiceDep,
) -> DocumentResponse:
    document = await service.create_document(payload)

    return DocumentResponse.model_validate(document)


@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    documents = await service.list_documents(
        limit=limit,
        offset=offset,
    )

    return [DocumentResponse.model_validate(document) for document in documents]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    service: ServiceDep,
) -> DocumentResponse:
    try:
        document = await service.get_document(document_id)

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        ) from exc

    return DocumentResponse.model_validate(document)
