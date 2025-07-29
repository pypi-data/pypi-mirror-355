import pytest
from allyin.multimodal2text import extract_text

def test_unsupported_filetype():
    with pytest.raises(ValueError):
        extract_text("unsupported_file.xyz")