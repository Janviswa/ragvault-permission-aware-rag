from pathlib import Path

import pytest

from app.documents.upload import validate_extension
from app.rag.loaders import load_text


def test_supported_extensions_are_accepted():
    assert validate_extension("report.txt") == ".txt"
    assert validate_extension("report.pdf") == ".pdf"
    assert validate_extension("report.docx") == ".docx"


def test_unsupported_extension_is_rejected():
    with pytest.raises(ValueError):
        validate_extension("malware.exe")


def test_txt_loader_reads_uploaded_text(tmp_path: Path):
    path = tmp_path / "document.txt"
    path.write_text("RAGVault test document", encoding="utf-8")

    assert load_text(str(path), ".txt") == "RAGVault test document"


def test_pdf_loader_extracts_text(tmp_path: Path):
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "document.pdf"

    pdf = canvas.Canvas(str(pdf_path))
    pdf.drawString(100, 750, "RAGVault PDF extraction test")
    pdf.save()

    text = load_text(str(pdf_path), ".pdf")

    assert "RAGVault PDF extraction test" in text

def test_docx_loader_extracts_text(tmp_path: Path):
    from docx import Document as DocxDocument

    docx_path = tmp_path / "document.docx"

    document = DocxDocument()
    document.add_paragraph("RAGVault DOCX extraction test")
    document.save(docx_path)

    text = load_text(str(docx_path), ".docx")

    assert "RAGVault DOCX extraction test" in text


def test_malformed_pdf_is_rejected(tmp_path: Path):
    pdf_path = tmp_path / "malformed.pdf"
    pdf_path.write_bytes(b"not a PDF")

    with pytest.raises(Exception):
        load_text(str(pdf_path), ".pdf")


def test_malformed_docx_is_rejected(tmp_path: Path):
    docx_path = tmp_path / "malformed.docx"
    docx_path.write_bytes(b"not a DOCX")

    with pytest.raises(Exception):
        load_text(str(docx_path), ".docx")