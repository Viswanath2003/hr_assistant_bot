# backend/app/rag/loader.py
import os
from typing import List, Dict, Tuple
from pypdf import PdfReader
from app.core.config import settings


def load_pdf_pages(file_path: str) -> List[Tuple[str, int]]:
    """
    Extract text per page from a PDF file.

    Returns:
        List of tuples: (page_text, page_number) ; page_number is 1-indexed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        pages.append((page_text.strip(), i + 1))

    return pages


def load_all_pdfs() -> List[Dict]:
    """
    Load all PDFs in RAW_DOCS_DIR and return a list of documents,
    each as: {"filename": <str>, "pages": [(text, page_no), ...]}
    """
    docs_dir = settings.RAW_DOCS_DIR
    pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf")]

    all_docs = []
    for pdf in pdf_files:
        path = os.path.join(docs_dir, pdf)
        print(f"📄 Loading PDF: {pdf}")
        pages = load_pdf_pages(path)
        all_docs.append({"filename": pdf, "pages": pages})

    return all_docs
