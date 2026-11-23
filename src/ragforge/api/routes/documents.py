from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ragforge.api.auth import CurrentUserDep
from ragforge.api.dependencies import get_document_service
from ragforge.core.responses import ApiResponse, success_response
from ragforge.schemas.document import (
    DocumentResponse,
)
from ragforge.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

ServiceDep = Annotated[
    DocumentService,
    Depends(get_document_service),
]


@router.get(
    "",
    response_model=ApiResponse[list[DocumentResponse]],
)
async def list_documents(
    service: ServiceDep,
    current_user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[DocumentResponse]]:
    documents = await service.list_documents(
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return success_response(
        data=[DocumentResponse.model_validate(document) for document in documents],
        message="Documents retrieved successfully",
    )


@router.get(
    "/{document_id}",
    response_model=ApiResponse[DocumentResponse],
)
async def get_document(
    document_id: UUID,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> ApiResponse[DocumentResponse]:
    document = await service.get_document(
        document_id=document_id,
        owner_id=current_user.id,
    )

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document retrieved successfully",
    )
