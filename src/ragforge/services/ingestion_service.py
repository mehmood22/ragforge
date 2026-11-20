import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ragforge.core.config import get_settings
from ragforge.core.handlers import logger
from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.ingestion.chunker import DocumentChunker
from ragforge.ingestion.embeddings import get_embedding_service
from ragforge.ingestion.pdf_loader import PDFLoader
from ragforge.models.document import Document, DocumentStatus
from ragforge.storage.base import FileStorage


class IngestionService:
    def __init__(
        self,
        session: AsyncSession,
        storage: FileStorage,
    ) -> None:
        self.session = session
        self.storage = storage
        self.settings = get_settings()

    async def ingest_pdf(
        self,
        document_id: UUID,
        storage_key: str,
    ) -> int:
        document = await self.session.get(Document, document_id)

        if document is None:
            raise ValueError("Document does not exist")

        document.status = DocumentStatus.PROCESSING.value
        await self.session.commit()

        collection = None

        try:
            loader = PDFLoader()
            chunker = DocumentChunker(
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            )

            content = await self.storage.download(storage_key)

            pages = await asyncio.to_thread(
                loader.load_bytes,
                content,
            )

            if not pages:
                raise ValueError("PDF contains no extractable text")

            if len(pages) > self.settings.max_pdf_pages:
                raise ValueError("PDF exceeds the pdf page limit")

            chunks = chunker.split(pages)

            texts = [chunk.text for chunk in chunks]

            def generate_embeddings() -> list[list[float]]:
                return get_embedding_service().embed_documents(texts)

            embeddings = await asyncio.to_thread(generate_embeddings)

            client = get_chroma_client()

            collection = await asyncio.to_thread(
                client.get_or_create_collection,
                name=self.settings.chroma_collection,
                metadata={
                    "embedding_model": self.settings.embedding_model,
                },
            )

            await asyncio.to_thread(
                collection.upsert,
                ids=[f"{document_id}:{chunk.chunk_index}" for chunk in chunks],
                documents=texts,
                embeddings=embeddings,  # type: ignore[arg-type]
                metadatas=[
                    {
                        "document_id": str(document_id),
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                    }
                    for chunk in chunks
                ],
            )

            document.chunk_count = len(chunks)
            document.status = DocumentStatus.INDEXED.value

            await self.session.commit()

            return len(chunks)

        except Exception:
            await self.session.rollback()

            # Compensate for a partial vector write.
            if collection is not None:
                try:
                    await asyncio.to_thread(
                        collection.delete,
                        where={"document_id": str(document_id)},
                    )
                except (RuntimeError, OSError):
                    logger.warning(
                        "Failed to clean up Chroma chunks for document_id=%s",
                        document_id,
                        exc_info=True,
                    )

            document.status = DocumentStatus.FAILED.value
            document.chunk_count = 0
            await self.session.commit()

            raise
