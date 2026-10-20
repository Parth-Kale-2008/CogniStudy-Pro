"""
CogniStudy Pro™ — Batch Indexing Utility.
Crawl a folder of documents (PDF, DOCX, TXT, MD, CSV) and build a FAISS vector index.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Safe UTF-8 console output for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from langchain_community.vectorstores import FAISS
from app.loaders.document_loader import DocumentProcessor
from app.rag.embeddings import get_embedding_provider
from app.core.logging import logger

load_dotenv()


def build_database(data_dir: str = "data", output_dir: str = "faiss_index"):
    """
    Scans data_dir for supported files, extracts text into semantic chunks,
    generates embeddings, and stores index in output_dir.
    """
    print("=" * 60)
    print("  [CogniStudy Pro] Batch Index Builder")
    print("=" * 60)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"[!] Created '{data_dir}' folder. Please place documents inside it.")
        return

    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=150)
    all_chunks = []
    processed_files = 0

    supported_exts = (".pdf", ".docx", ".doc", ".txt", ".md", ".csv")

    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.lower().endswith(supported_exts):
                file_path = os.path.join(root, file)
                print(f"  -> Processing: {file} ...", end=" ", flush=True)
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    chunks, meta = processor.extract_from_bytes(content, file)
                    all_chunks.extend(chunks)
                    processed_files += 1
                    print(f"OK ({len(chunks)} chunks)")
                except Exception as e:
                    print(f"FAILED ({e})")

    if not all_chunks:
        print("\n[!] No extractable chunks found. Place supported files (.pdf, .docx, .txt) in data/ folder.")
        return

    print("\n[+] Summary:")
    print(f"  * Files Processed: {processed_files}")
    print(f"  * Total Chunks Created: {len(all_chunks)}")
    print(f"  * Generating Embeddings & Building FAISS Vector Index...")

    embeddings = get_embedding_provider()
    db = FAISS.from_documents(all_chunks, embeddings)

    os.makedirs(output_dir, exist_ok=True)
    db.save_local(output_dir)

    print("\n[OK] FAISS Vector Database Successfully Created!")
    print(f"     Stored in: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build FAISS vector index from documents folder.")
    parser.add_argument("--data-dir", default="data", help="Directory containing documents (default: data)")
    parser.add_argument("--output-dir", default="faiss_index", help="Output directory for FAISS index (default: faiss_index)")
    args = parser.parse_args()

    build_database(data_dir=args.data_dir, output_dir=args.output_dir)