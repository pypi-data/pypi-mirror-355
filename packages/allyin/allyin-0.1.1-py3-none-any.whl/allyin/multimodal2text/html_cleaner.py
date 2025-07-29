



from .data_cleaner import clean_text  # Import the cleaner
from readability import Document
from bs4 import BeautifulSoup

def clean_html(html_content: str) -> str:
    """
    Extracts and returns the main content from raw HTML using readability-lxml.
    """
    doc = Document(html_content)
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "html.parser")
    return clean_text(soup.get_text(separator="\n", strip=True))  # Clean the extracted text