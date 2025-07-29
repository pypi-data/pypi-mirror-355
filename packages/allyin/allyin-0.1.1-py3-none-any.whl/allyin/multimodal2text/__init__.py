

"""
multimodal2text

Unified text extraction interface for PDFs, images, audio, slides, and HTML files.
"""

from .dispatcher import extract_text
from .data_cleaner import clean_text

__all__ = ["extract_text", "clean_text"]