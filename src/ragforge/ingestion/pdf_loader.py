from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass(frozen=True)
class PageContent:
    page_number: int
    text: str


class PDFLoader:
    def load_bytes(self, content: bytes) -> list[PageContent]:
        reader = PdfReader(BytesIO(content), strict=True)

        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported")

        pages: list[PageContent] = []

        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            if text.strip():
                pages.append(
                    PageContent(
                        page_number=index + 1,
                        text=text.strip(),
                    )
                )

        return pages
