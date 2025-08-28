import io
import os
import tempfile
from typing import Optional, Tuple

from gtts import gTTS
from pydub import AudioSegment

# ---- TTS ----
def tts_to_bytes(text: str) -> bytes:
    """Text → MP3 bytes (gTTS)."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as f:
        gTTS(text).save(f.name)
        audio = AudioSegment.from_file(f.name, format="mp3")
        buf = io.BytesIO()
        audio.export(buf, format="mp3")
        return buf.getvalue()

# ---- STT (faster-whisper) ----
_WHISPER_MODEL = None

def _get_whisper():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        model_size = os.getenv("STT_MODEL", "base.en")
        # Use float32 on CPU for broad compatibility; set compute_type to "int8" if you want extra speed
        _WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type="float32")
    return _WHISPER_MODEL

def transcribe_audio_bytes(wav_or_mp3_bytes: bytes, language: Optional[str] = "en") -> str:
    """
    Accepts WAV/MP3 bytes, returns transcription text.
    We convert to WAV (16k mono) for stable decoding.
    """
    # Normalize to WAV mono 16k
    audio = AudioSegment.from_file(io.BytesIO(wav_or_mp3_bytes))
    audio = audio.set_channels(1).set_frame_rate(16000)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    buf.seek(0)

    model = _get_whisper()
    segments, _info = model.transcribe(buf, language=language)
    text_parts = [seg.text for seg in segments]
    return " ".join(t.strip() for t in text_parts).strip()
