from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PageContent:
    page_number: int
    text: str


class PDFLoader:
    def load(self, file_path: Path) -> list[PageContent]:
        reader = PdfReader(str(file_path), strict=True)

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
