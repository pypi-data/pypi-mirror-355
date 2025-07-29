import os
from .pdf_parser import extract_text_from_pdf
from .image_ocr import extract_text_from_image
from .audio_transcriber import transcribe_audio
from .slide_parser import extract_text_from_pptx
from .html_cleaner import clean_html
from .docx_parser import extract_text_from_docx
from .excel_parser import extract_text_from_excel
from .utils import detect_filetype
# The following import should be relative:
# from multimodal2text.data_cleaner import clean_text
from .data_cleaner import clean_text


def extract_text(file_path: str) -> str:
    """
    Dispatch function to extract text from a file by type.
    Supports: PDF, image, audio, PowerPoint, HTML, Word, Excel
    """
    filetype = detect_filetype(file_path)

    if filetype == "pdf":
        return extract_text_from_pdf(file_path)
    elif filetype == "image":
        return extract_text_from_image(file_path)
    elif filetype == "audio":
        return transcribe_audio(file_path)
    elif filetype == "pptx":
        return extract_text_from_pptx(file_path)
    elif filetype == "html":
        with open(file_path, "r", encoding="utf-8") as f:
            return clean_html(f.read())
    elif filetype == "docx":
        return extract_text_from_docx(file_path)
    elif filetype == "xlsx":
        return extract_text_from_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {filetype}")