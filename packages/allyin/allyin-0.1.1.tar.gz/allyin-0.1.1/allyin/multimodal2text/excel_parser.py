import pandas as pd

def extract_text_from_excel(file_path: str) -> str:
    """
    Extracts text from an Excel file by reading all sheets and converting to plain text.
    """
    try:
        xls = pd.read_excel(file_path, sheet_name=None)  # load all sheets
        content = []
        for sheet_name, df in xls.items():
            content.append(f"Sheet: {sheet_name}\n")
            content.append(df.to_string(index=False))
            content.append("\n")
        return "\n".join(content)
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from Excel file: {e}")