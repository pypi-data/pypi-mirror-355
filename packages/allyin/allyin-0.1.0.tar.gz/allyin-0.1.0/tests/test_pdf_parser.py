

import os
import pytest
from allyin.multimodal2text.pdf_parser import extract_text_from_pdf

def test_extract_text_from_pdf():
    sample_path = "tests/sample_files/sample.pdf"
    if not os.path.exists(sample_path):
        pytest.skip("Sample PDF not available for test")
    text = extract_text_from_pdf(sample_path)
    assert isinstance(text, str)
    assert len(text.strip()) > 0