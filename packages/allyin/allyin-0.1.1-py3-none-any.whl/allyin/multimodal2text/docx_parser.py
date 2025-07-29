from docx import Document
from .data_cleaner import clean_text

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    return clean_text(full_text)