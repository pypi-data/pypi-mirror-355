import os
from allyin.multimodal2text.excel_parser import extract_text_from_excel

def test_extract_text_from_excel():
    sample_file = "tests/sample_files/sample.xlsx"
    assert os.path.exists(sample_file), "sample.xlsx not found in sample_files"

    text = extract_text_from_excel(sample_file)
    assert isinstance(text, str), "Output should be a string"
    assert len(text.strip()) > 0, "Extracted text is empty"
    print("\nExtracted Excel content:\n", text)