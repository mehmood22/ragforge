from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ragforge.ingestion.pdf_loader import PageContent


@dataclass(frozen=True)
class TextChunk:
    page_number: int
    chunk_index: int
    text: str


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        if chunk_size <= 0 or not 0 <= chunk_overlap < chunk_size:
            raise ValueError("Invalid chunk configuration")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split(self, pages: list[PageContent]) -> list[TextChunk]:
        chunks: list[TextChunk] = []

        for page in pages:
            parts = self.splitter.split_text(page.text)

            for part in parts:
                chunks.append(
                    TextChunk(
                        page_number=page.page_number,
                        chunk_index=len(chunks),
                        text=part,
                    )
                )

        return chunks
