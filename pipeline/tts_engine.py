"""
pipeline/tts_engine.py
Text-to-Speech engine — supports Google Cloud TTS (default) and ElevenLabs.
Provider is selected via TTS_PROVIDER env var ("google" | "elevenlabs").

Returns:
  audio_path : Path   — path to generated .mp3 file
  duration   : float  — total audio duration in seconds
"""

import os
import logging
import subprocess
from pathlib import Path

from pipeline.config import (
    TTS_PROVIDER,
    GOOGLE_TTS_VOICE, GOOGLE_TTS_LANG,
    ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL,
    OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


# ─── Google Cloud TTS ─────────────────────────────────────────────────────────

def _synthesize_google(text: str, output_path: Path) -> None:
    """Uses Google Cloud Text-to-Speech (WaveNet). Free up to 1M chars/month."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=GOOGLE_TTS_LANG,
        name=GOOGLE_TTS_VOICE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.05,    # Slightly faster — energetic feel
        pitch=1.0,
        effects_profile_id=["headphone-class-device"],
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.audio_content)

    logger.info(f"Google TTS: saved to {output_path}")


# ─── ElevenLabs TTS ───────────────────────────────────────────────────────────

def _synthesize_elevenlabs(text: str, output_path: Path) -> None:
    """Uses ElevenLabs SDK. Requires ELEVENLABS_API_KEY env var."""
    from elevenlabs.client import ElevenLabs

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise EnvironmentError("ELEVENLABS_API_KEY not set")

    client = ElevenLabs(api_key=api_key)

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL,
        output_format="mp3_22050_32",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)

    logger.info(f"ElevenLabs TTS: saved to {output_path}")


# ─── Audio duration helper ────────────────────────────────────────────────────

def _get_audio_duration(audio_path: Path) -> float:
    """Uses ffprobe to get precise audio duration in seconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        logger.warning("Could not parse ffprobe output; defaulting to 45.0s")
        return 45.0


# ─── Public interface ─────────────────────────────────────────────────────────

def synthesize(text: str, filename: str = "narration.mp3") -> tuple[Path, float]:
    """
    Synthesize text to speech using the configured provider.

    Args:
        text     : Narration text to convert
        filename : Output filename (saved inside OUTPUT_DIR)

    Returns:
        (audio_path, duration_seconds)
    """
    output_path = OUTPUT_DIR / filename
    provider    = TTS_PROVIDER.lower()

    logger.info(f"TTS provider: {provider} | chars: {len(text)}")

    if provider == "elevenlabs":
        _synthesize_elevenlabs(text, output_path)
    else:
        # Default: Google Cloud TTS
        _synthesize_google(text, output_path)

    duration = _get_audio_duration(output_path)
    logger.info(f"Audio duration: {duration:.2f}s")

    return output_path, duration


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "Did you know you can write a professional email in just 30 seconds using ChatGPT? "
        "Here's how. Open ChatGPT, type: Write a polite follow-up email to my client about "
        "the pending invoice. Add any details you want, then hit enter. In seconds, you get a "
        "perfectly worded, professional email ready to copy and send. No more staring at a blank "
        "screen. Subscribe for one AI productivity hack every single day!"
    )
    path, dur = synthesize(sample, "test_narration.mp3")
    print(f"Saved: {path} | Duration: {dur:.2f}s")
