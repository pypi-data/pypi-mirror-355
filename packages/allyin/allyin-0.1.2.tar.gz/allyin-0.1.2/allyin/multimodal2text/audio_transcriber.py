

import whisper
from .data_cleaner import clean_text  # Import the cleaner

model = whisper.load_model("base")

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes and returns cleaned text from an audio file using Whisper.
    Supported formats: MP3, WAV, M4A, FLAC, etc.
    """
    result = model.transcribe(file_path)
    return clean_text(result["text"])  # Clean the transcription