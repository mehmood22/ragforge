from ragforge.ingestion.chunker import DocumentChunker
from ragforge.ingestion.pdf_loader import PageContent


def test_chunker_preserves_page_numbers() -> None:
    pages = [
        PageContent(
            page_number=3,
            text="International roaming charges apply. " * 30,
        )
    ]

    chunker = DocumentChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.split(pages)

    assert len(chunks) > 1
    assert all(chunk.page_number == 3 for chunk in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_empty_pages_produce_no_chunks() -> None:
    chunker = DocumentChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    assert chunker.split([]) == []
