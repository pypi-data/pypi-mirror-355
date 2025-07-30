from PIL import Image
import pytesseract
from .data_cleaner import clean_text  # Add import at the top

def extract_text_from_image(file_path: str) -> str:
    """
    Extracts and returns cleaned text from an image using Tesseract OCR.
    Supported formats: PNG, JPG, JPEG, TIFF, BMP
    """
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return clean_text(text)  # Clean the OCR output
