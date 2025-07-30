import fitz  # PyMuPDF
from .data_cleaner import clean_text  # Import the cleaner

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts and returns cleaned text from a PDF file using PyMuPDF.
    """
    text = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text.append(page.get_text())
    raw_text = "\n".join(text)
    return clean_text(raw_text)  # Apply cleaning before returning