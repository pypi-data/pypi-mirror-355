

# Allyin: Modular Multimodal Extractor

Allyin is a Python library that extracts text from various file formats including PDFs, DOCX, XLSX, PPTX, images, HTML, and audio.

## Installation

First, ensure that `openai-whisper` is installed (used for audio transcription):

```bash
pip install git+https://github.com/openai/whisper.git
```

Then install Allyin:

```bash
pip install allyin
```

> Note: You may need to install system dependencies like `ffmpeg` for Whisper and `tesseract` for OCR.

## Usage

### Import

```python
from allyin.multimodal2text import extract_text
```

### Supported File Types

| Format      | Description               |
|-------------|---------------------------|
| `.pdf`      | Extracts text from PDFs   |
| `.docx`     | Extracts text from Word   |
| `.xlsx`     | Extracts text from Excel  |
| `.pptx`     | Extracts text from Slides |
| `.png/jpg`  | OCR-based text extraction |
| `.html`     | Extracts visible content  |
| `.mp3/.wav` | Transcribes audio         |

### Example

```python
from allyin.multimodal2text import extract_text

result = extract_text("/path/to/your/file.pdf")
print(result["text"])
```

## License

MIT