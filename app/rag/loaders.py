"""Document text extraction adapters."""

from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def load_text(file_path: str, extension: str) -> str:
    extension = extension.lower()

    if extension == ".txt":
        return Path(file_path).read_text(encoding="utf-8")

    if extension == ".pdf":
        reader = PdfReader(file_path)

        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)

        return "\n\n".join(pages)

    if extension == ".docx":
        document = DocxDocument(file_path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    raise ValueError(f"Unsupported document type: {extension}")