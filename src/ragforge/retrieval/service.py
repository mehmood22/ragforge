import asyncio
from functools import lru_cache
from uuid import UUID

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import get_settings
from ragforge.core.exceptions import (
    ConflictException,
    DocumentNotFoundException,
)
from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.infrastructure.collection import validate_collection
from ragforge.models.document import Document, DocumentStatus
from ragforge.retrieval.scoring import squared_l2_to_relevance
from ragforge.schemas.retrieval import RetrievedChunk


@lru_cache(maxsize=1)
@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    settings = get_settings()
    client = get_chroma_client()

    collection = client.get_collection(
        name=settings.chroma_collection,
    )

    validate_collection(
        metadata=collection.metadata,
        configuration=collection.configuration,
        expected_embedding_model=settings.embedding_model,
    )

    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )

    return Chroma(
        client=client,
        collection_name=settings.chroma_collection,
        embedding_function=embeddings,
        relevance_score_fn=squared_l2_to_relevance,
        create_collection_if_not_exists=False,
    )


class RetrievalService:
    def __init__(
        self,
        session: AsyncSession,
        vector_store: Chroma,
    ) -> None:
        self.session = session
        self.vector_store = vector_store

    async def search(
        self,
        document_id: UUID,
        query: str,
        top_k: int,
        min_score: float,
    ) -> list[RetrievedChunk]:
        document = await self.session.get(Document, document_id)

        if document is None:
            raise DocumentNotFoundException()

        if (
            document.status != DocumentStatus.INDEXED.value
            or document.indexed_generation is None
        ):
            raise ConflictException("Document is not ready for retrieval")

        filters = {
            "$and": [
                {"document_id": str(document_id)},
                {"generation_id": str(document.indexed_generation)},
            ]
        }

        results = await asyncio.to_thread(
            self.vector_store.similarity_search_with_relevance_scores,
            query,
            k=top_k,
            filter=filters,
            score_threshold=min_score,
        )

        chunks: list[RetrievedChunk] = []

        for source, score in results:
            metadata = source.metadata

            chunks.append(
                RetrievedChunk(
                    content=source.page_content,
                    document_id=document_id,
                    page_number=int(metadata["page_number"]),
                    chunk_index=int(metadata["chunk_index"]),
                    score=float(score),
                )
            )

        return chunks
