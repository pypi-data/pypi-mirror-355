import re

def clean_text(text: str) -> str:
    """
    Cleans extracted text by removing headers, footers, excessive whitespace, and noise.
    """
    # Remove common unicode noise
    text = text.replace("\ufeff", "").replace("\u200b", "")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)               # collapse multiple spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)            # collapse 3+ newlines to 2
    text = text.strip()

    # Remove repeated headers/footers (basic pattern)
    lines = text.splitlines()
    cleaned_lines = []
    last_line = None
    for line in lines:
        line = line.strip()
        if line and line != last_line:
            cleaned_lines.append(line)
            last_line = line
    return "\n".join(cleaned_lines)