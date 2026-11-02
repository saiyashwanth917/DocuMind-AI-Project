from pathlib import Path
from .pdf_loader import extract_pdf
from .word_loader import extract_docx
from .ppt_loader import extract_pptx

def extract_document(path):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".pptx":
        return extract_pptx(path)
    raise ValueError("Supported formats are PDF, DOCX and PPTX. Convert legacy DOC/PPT files first.")
