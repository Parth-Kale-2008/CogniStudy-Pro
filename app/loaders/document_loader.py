"""
Multi-format Document Loader and Preprocessor.
Supports PDF, DOCX, TXT, MD, CSV with semantic chunking and page metadata.
"""

import io
import os
import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging import logger
from app.config import settings


class DocumentProcessor:
    """
    Robust processor that accepts raw bytes or file paths and outputs
    LangChain Documents with enriched metadata (page, source, doc_id, chunk_index).
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def extract_from_bytes(self, content: bytes, filename: str) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Parses raw bytes based on filename extension and splits into semantic chunks.
        Returns (chunks, document_metadata).
        """
        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        pages: List[Tuple[int, str]] = []

        try:
            if ext == ".pdf":
                pages = self._extract_pdf(content)
            elif ext in [".docx", ".doc"]:
                pages = self._extract_docx(content)
            elif ext in [".txt", ".md", ".csv", ".json", ".log"]:
                pages = self._extract_text(content)
            else:
                # Default fallback: attempt text decoding
                pages = self._extract_text(content)
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {e}", exc_info=True)
            raise ValueError(f"Failed to parse document '{filename}': {str(e)}")

        if not pages or all(not text.strip() for _, text in pages):
            logger.warning(f"No readable text extracted from {filename}")
            return [], {
                "doc_id": doc_id,
                "filename": filename,
                "file_type": ext,
                "file_size_bytes": len(content),
                "chunk_count": 0,
                "upload_timestamp": datetime.utcnow().isoformat()
            }

        chunks: List[Document] = []
        chunk_counter = 0

        for page_num, text in pages:
            if not text.strip():
                continue
            split_docs = self.text_splitter.create_documents(
                texts=[text],
                metadatas=[{
                    "source": filename,
                    "page": page_num,
                    "doc_id": doc_id,
                    "file_type": ext,
                }]
            )
            for doc in split_docs:
                doc.metadata["chunk_id"] = chunk_counter
                chunks.append(doc)
                chunk_counter += 1

        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": ext,
            "file_size_bytes": len(content),
            "chunk_count": len(chunks),
            "upload_timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Processed '{filename}': extracted {len(pages)} pages -> {len(chunks)} chunks")
        return chunks, metadata

    def _extract_pdf(self, content: bytes) -> List[Tuple[int, str]]:
        pages: List[Tuple[int, str]] = []
        # Primary: PyMuPDF
        try:
            import pymupdf
            doc = pymupdf.open(stream=content, filetype="pdf")
            max_pages = min(len(doc), 100)
            for page_idx in range(max_pages):
                page_text = doc[page_idx].get_text().strip()
                if page_text:
                    pages.append((page_idx + 1, page_text))
            if pages:
                return pages
        except Exception as e:
            logger.warning(f"PyMuPDF failed on PDF, attempting pypdf fallback: {e}")

        # Secondary: pypdf fallback
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            for page_idx, page in enumerate(reader.pages[:100]):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append((page_idx + 1, text.strip()))
        except Exception as e:
            logger.error(f"Both PDF extractors failed: {e}")
            raise

        return pages

    def _extract_docx(self, content: bytes) -> List[Tuple[int, str]]:
        import docx
        doc = docx.Document(io.BytesIO(content))
        full_text = []

        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    full_text.append(row_text)

        joined = "\n\n".join(full_text)
        return [(1, joined)] if joined else []

    def _extract_text(self, content: bytes) -> List[Tuple[int, str]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        text = None
        for enc in encodings:
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            text = content.decode("utf-8", errors="replace")

        return [(1, text)]
