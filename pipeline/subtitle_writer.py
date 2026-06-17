"""
pipeline/subtitle_writer.py
Converts a narration script into a timed .srt subtitle file.
Uses word-count-based timing (since Google TTS doesn't return word timestamps
on the free tier). For ElevenLabs alignment is approximate but visually good.

Output: Path to .srt file
"""

import math
import logging
import re
from pathlib import Path
from pipeline.config import OUTPUT_DIR

logger = logging.getLogger(__name__)

WORDS_PER_SECOND = 2.6   # Average spoken English pace (~156 WPM)
MAX_WORDS_PER_LINE = 7   # Subtitle line length


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert float seconds → SRT timestamp format HH:MM:SS,mmm"""
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = int(seconds % 60)
    millis  = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _chunk_words(words: list[str], chunk_size: int) -> list[list[str]]:
    """Split word list into chunks of ~chunk_size words."""
    return [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]


def generate_srt(narration: str, audio_duration: float, output_filename: str = "captions.srt") -> Path:
    """
    Generates a .srt subtitle file from narration text.

    Args:
        narration       : Full narration text
        audio_duration  : Total audio duration in seconds (from tts_engine)
        output_filename : Name of the output .srt file

    Returns:
        Path to the generated .srt file
    """
    output_path = OUTPUT_DIR / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean text
    text   = re.sub(r'\s+', ' ', narration).strip()
    words  = text.split()
    chunks = _chunk_words(words, MAX_WORDS_PER_LINE)

    # Calculate timing — distribute chunks proportionally across audio duration
    total_words = len(words)
    srt_lines   = []

    current_time = 0.0
    for idx, chunk in enumerate(chunks, start=1):
        chunk_words = len(chunk)
        # Proportional duration based on word count
        chunk_duration = (chunk_words / total_words) * audio_duration

        start = current_time
        end   = min(current_time + chunk_duration, audio_duration)

        srt_lines.append(
            f"{idx}\n"
            f"{_seconds_to_srt_time(start)} --> {_seconds_to_srt_time(end)}\n"
            f"{' '.join(chunk)}\n"
        )
        current_time = end

    srt_content = "\n".join(srt_lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    logger.info(f"SRT generated: {output_path} ({len(chunks)} subtitle blocks)")
    return output_path


def srt_to_moviepy_subtitles(srt_path: Path) -> list[dict]:
    """
    Parse .srt file into a list of dicts for MoviePy rendering.

    Returns list of:
      { 'start': float, 'end': float, 'text': str }
    """
    subs = []
    content = srt_path.read_text(encoding="utf-8")
    blocks  = content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        # lines[0] = index, lines[1] = timestamps, lines[2:] = text
        times = lines[1].split(" --> ")
        start = _srt_time_to_seconds(times[0].strip())
        end   = _srt_time_to_seconds(times[1].strip())
        text  = " ".join(lines[2:])
        subs.append({"start": start, "end": end, "text": text})

    return subs


def _srt_time_to_seconds(srt_time: str) -> float:
    """Convert SRT timestamp HH:MM:SS,mmm → float seconds"""
    srt_time = srt_time.replace(",", ".")
    parts    = srt_time.split(":")
    hours    = float(parts[0])
    minutes  = float(parts[1])
    seconds  = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "Did you know you can write a professional email in just 30 seconds using ChatGPT? "
        "Open ChatGPT and type your instruction. Add the key details you need. "
        "Hit enter and get a perfect email instantly. "
        "Subscribe for one AI hack every single day!"
    )
    p = generate_srt(sample, 42.5, "test_captions.srt")
    print(f"Saved: {p}")
    print(srt_to_moviepy_subtitles(p))
