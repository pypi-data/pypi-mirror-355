# tests/test_docx_parser.py
from allyin.multimodal2text.docx_parser import extract_text_from_docx

def test_extract_text_from_docx():
    text = extract_text_from_docx("tests/sample_files/sample.docx")
    print(text)
    assert isinstance(text, str)
    assert len(text.strip()) > 0