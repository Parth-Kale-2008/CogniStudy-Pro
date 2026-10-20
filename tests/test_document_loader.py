"""
Unit tests for DocumentProcessor and multi-format loaders.
"""

from app.loaders.document_loader import DocumentProcessor


def test_txt_loading(sample_txt_bytes):
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
    chunks, meta = processor.extract_from_bytes(sample_txt_bytes, "test.txt")

    assert len(chunks) > 0
    assert meta["filename"] == "test.txt"
    assert meta["file_type"] == ".txt"
    assert chunks[0].metadata["source"] == "test.txt"
    assert chunks[0].metadata["page"] == 1


def test_pdf_loading_multipage(sample_pdf_bytes):
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    chunks, meta = processor.extract_from_bytes(sample_pdf_bytes, "research_paper.pdf")

    assert len(chunks) >= 2
    assert meta["file_type"] == ".pdf"
    pages = [c.metadata["page"] for c in chunks]
    assert 1 in pages
    assert 2 in pages


def test_docx_loading(sample_docx_bytes):
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    chunks, meta = processor.extract_from_bytes(sample_docx_bytes, "lecture_notes.docx")

    assert len(chunks) > 0
    assert meta["file_type"] == ".docx"
    assert "Neural networks" in chunks[0].page_content


def test_empty_content():
    processor = DocumentProcessor()
    chunks, meta = processor.extract_from_bytes(b"", "empty.txt")
    assert len(chunks) == 0
    assert meta["chunk_count"] == 0
