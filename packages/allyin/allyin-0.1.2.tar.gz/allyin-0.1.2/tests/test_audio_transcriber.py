

import os
import pytest
from allyin.multimodal2text.audio_transcriber import transcribe_audio

def test_transcribe_audio():
    sample_path = "tests/sample_files/sample_audio.wav"
    if not os.path.exists(sample_path):
        pytest.skip("Sample audio not available for test")
    text = transcribe_audio(sample_path)
    assert isinstance(text, str)
    assert len(text.strip()) > 0