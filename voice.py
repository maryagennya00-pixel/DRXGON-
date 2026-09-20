# ============================================
# arya/voice.py
# ARYA Voice Layer — Whisper input + TTS output
# ============================================

import warnings
warnings.filterwarnings("ignore")

from groq import Groq
from config import GROQ_API_KEY, WHISPER_MODEL
import os, re, tempfile, requests

groq_client = Groq(api_key=GROQ_API_KEY)


# ── WHISPER TRANSCRIPTION ─────────────────────

def transcribe_file(audio_path: str) -> dict:
    """
    Transcribe an audio file using Groq Whisper.
    Supports: mp3, mp4, wav, m4a, webm, ogg
    Returns: text, language, duration
    """
    if not os.path.exists(audio_path):
        return {"error": f"File not found: {audio_path}",
                "text": "", "language": "unknown"}

    print(f"  [Whisper] Transcribing: {os.path.basename(audio_path)}")

    try:
        with open(audio_path, "rb") as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                response_format="verbose_json",
            )

        text     = transcript.text.strip()
        language = getattr(transcript, 'language', 'unknown')
        duration = getattr(transcript, 'duration', 0)

        print(f"  [Whisper] Transcript: '{text[:80]}'")
        print(f"  [Whisper] Language: {language} | Duration: {duration:.1f}s")

        return {
            "text":     text,
            "language": language,
            "duration": round(duration, 1),
            "error":    None
        }

    except Exception as e:
        return {"error": str(e), "text": "", "language": "unknown"}


def transcribe_url(audio_url: str) -> dict:
    """Download audio from URL then transcribe"""
    try:
        print(f"  [Whisper] Downloading from URL...")
        response = requests.get(audio_url, timeout=30)
        response.raise_for_status()

        ext = audio_url.split('.')[-1].split('?')[0]
        if ext not in ['mp3', 'mp4', 'wav', 'm4a', 'webm', 'ogg']:
            ext = 'mp3'

        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        result = transcribe_file(tmp_path)
        os.unlink(tmp_path)
        return result

    except Exception as e:
        return {"error": str(e), "text": "", "language": "unknown"}


# ── TEXT TO SPEECH ────────────────────────────
# Uses Groq's own Orpheus TTS — same GROQ_API_KEY, no ElevenLabs key needed.
# Returns raw audio bytes in memory — nothing is written to disk.

def _split_for_tts(text: str, limit: int = 200) -> list:
    """Split text into <=limit-char chunks on sentence (then word) boundaries.
    Orpheus accepts short inputs per request (~200 chars), so longer replies are chunked."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, cur = [], ""
    for s in sentences:
        while len(s) > limit:                      # very long sentence: split on words
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if cur:
                chunks.append(cur); cur = ""
            chunks.append(s[:cut].strip()); s = s[cut:].strip()
        if len(cur) + len(s) + 1 <= limit:
            cur = f"{cur} {s}".strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


def _join_wavs(parts: list) -> bytes:
    """Concatenate WAV byte strings (same format) into one WAV."""
    import io, wave
    if len(parts) == 1:
        return parts[0]
    out = io.BytesIO()
    with wave.open(out, "wb") as w_out:
        for i, data in enumerate(parts):
            with wave.open(io.BytesIO(data), "rb") as w_in:
                if i == 0:
                    w_out.setparams(w_in.getparams())
                w_out.writeframes(w_in.readframes(w_in.getnframes()))
    return out.getvalue()


def text_to_speech(text: str,
                    voice: str = "hannah",
                    speed: float = 0.95,
                    max_chunks: int = 4) -> dict:
    """
    Convert DRXGON's response to speech using Groq's Orpheus TTS.
    Voices: autumn, diana, hannah, austin, daniel, troy
    Long text is split into chunks (max_chunks) and stitched into one WAV.
    Returns audio as in-memory bytes (key "audio_bytes") — never saved to disk.
    """
    try:
        parts = []
        for chunk in _split_for_tts(text)[:max_chunks]:
            response = groq_client.audio.speech.create(
                model="canopylabs/orpheus-v1-english",
                voice=voice,
                input=chunk,
                speed=speed,
                response_format="wav"
            )
            parts.append(response.read())

        if not parts:
            return {"success": False, "message": "Nothing to speak", "text": text}

        audio_bytes = _join_wavs(parts)
        print(f"  [TTS] Audio generated: {len(audio_bytes)} bytes from {len(parts)} chunk(s)")
        return {"success": True, "audio_bytes": audio_bytes, "text": text}

    except Exception as e:
        print(f"  [TTS] Failed: {e}")
        return {"success": False, "message": str(e), "text": text}


def clean_for_tts(text: str) -> str:
    """
    Clean markdown formatting before sending to TTS.
    TTS reads asterisks and hashes aloud — remove them.
    """
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'```[\s\S]+?```', '[code block]', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── VOICE PIPELINE ────────────────────────────

def voice_input_to_text(audio_path: str = None, audio_url: str = None) -> dict:
    """Complete voice input pipeline. Accepts file path or URL."""
    if audio_path:
        return transcribe_file(audio_path)
    elif audio_url:
        return transcribe_url(audio_url)
    else:
        return {"error": "No audio source provided", "text": ""}