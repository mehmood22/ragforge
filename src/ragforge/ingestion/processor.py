import asyncio
from collections.abc import Sequence
from typing import cast
from uuid import UUID

from ragforge.core.config import Settings
from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.ingestion.chunker import DocumentChunker
from ragforge.ingestion.embeddings import get_embedding_service
from ragforge.ingestion.pdf_loader import PDFLoader
from ragforge.storage.base import FileStorage


class PDFProcessor:
    def __init__(
        self,
        storage: FileStorage,
        settings: Settings,
    ) -> None:
        self.storage = storage
        self.settings = settings
        self.loader = PDFLoader()
        self.chunker = DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def process(
        self,
        document_id: UUID,
        generation_id: UUID,
        storage_key: str,
    ) -> int:
        content = await self.storage.download(storage_key)

        pages = await asyncio.to_thread(
            self.loader.load_bytes,
            content,
        )

        if not pages:
            raise ValueError("PDF has no extractable text")

        if len(pages) > 100:
            raise ValueError("PDF exceeds the page limit")

        chunks = self.chunker.split(pages)

        if not chunks:
            raise ValueError("PDF has no usable text")

        client = get_chroma_client()

        collection = await asyncio.to_thread(
            client.get_or_create_collection,
            name=self.settings.chroma_collection,
            metadata={
                "embedding_model": self.settings.embedding_model,
            },
        )

        batch_size = 32

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [chunk.text for chunk in batch]

            def generate_embeddings(batch_texts: list[str]) -> list[list[float]]:
                return get_embedding_service().embed_documents(batch_texts)

            vectors = await asyncio.to_thread(generate_embeddings, texts)

            await asyncio.to_thread(
                collection.upsert,
                ids=[
                    f"{document_id}:{generation_id}:{chunk.chunk_index}"
                    for chunk in batch
                ],
                documents=texts,
                embeddings=cast(list[Sequence[float]], vectors),
                metadatas=[
                    {
                        "document_id": str(document_id),
                        "generation_id": str(generation_id),
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                    }
                    for chunk in batch
                ],
            )

        return len(chunks)
