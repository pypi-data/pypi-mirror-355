

import os
import pytest
from allyin.multimodal2text.slide_parser import extract_text_from_pptx

def test_extract_text_from_pptx():
    sample_path = "tests/sample_files/sample_slide.pptx"
    if not os.path.exists(sample_path):
        pytest.skip("Sample slide not available for test")
    text = extract_text_from_pptx(sample_path)
    assert isinstance(text, str)
    assert len(text.strip()) > 0