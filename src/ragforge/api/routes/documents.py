from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ragforge.api.dependencies import get_document_service
from ragforge.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from ragforge.services.document_service import (
    DocumentService,
)
from ragforge.core.responses import (
    ApiResponse,
    success_response,
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
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: DocumentCreate,
    service: ServiceDep,
) -> ApiResponse[DocumentResponse]:
    document = await service.create_document(payload)

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document created successfully",
    )


@router.get(
    "",
    response_model=ApiResponse[list[DocumentResponse]],
)
async def list_documents(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[DocumentResponse]]:
    documents = await service.list_documents(
        limit=limit,
        offset=offset,
    )

    return success_response(
        data=[
            DocumentResponse.model_validate(document)
            for document in documents
        ],
        message="Documents retrieved successfully",
    )

@router.get(
    "/{document_id}",
    response_model=ApiResponse[DocumentResponse],
)
async def get_document(
    document_id: UUID,
    service: ServiceDep,
) -> ApiResponse[DocumentResponse]:
    document = await service.get_document(document_id)

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document retrieved successfully",
    )
