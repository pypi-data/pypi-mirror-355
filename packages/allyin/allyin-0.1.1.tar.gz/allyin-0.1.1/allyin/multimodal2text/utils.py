import os
import mimetypes

def detect_filetype(file_path: str) -> str:
    """
    Determines the file type based on extension or MIME type.
    Returns: 'pdf', 'image', 'audio', 'pptx', 'html', 'docx', 'xlsx', or raises ValueError.
    """
    ext = os.path.splitext(file_path)[-1].lower()

    if ext in [".pdf"]:
        return "pdf"
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return "image"
    elif ext in [".mp3", ".wav", ".m4a", ".aac", ".flac"]:
        return "audio"
    elif ext in [".pptx"]:
        return "pptx"
    elif ext in [".html", ".htm"]:
        return "html"
    elif ext in [".docx"]:
        return "docx"
    elif ext in [".xlsx"]:
        return "xlsx"
    else:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith("image/"):
                return "image"
            elif mime_type.startswith("audio/"):
                return "audio"
            elif mime_type == "application/pdf":
                return "pdf"
            elif mime_type in ("text/html", "application/xhtml+xml"):
                return "html"
        raise ValueError(f"Could not determine file type for: {file_path}")