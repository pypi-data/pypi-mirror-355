

import os
import pytest
from allyin.multimodal2text.image_ocr import extract_text_from_image

def test_extract_text_from_image():
    sample_path = "tests/sample_files/sample_image.png"
    if not os.path.exists(sample_path):
        pytest.skip("Sample image not available for test")
    text = extract_text_from_image(sample_path)
    assert isinstance(text, str)
    assert len(text.strip()) > 0