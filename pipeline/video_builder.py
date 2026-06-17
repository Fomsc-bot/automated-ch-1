"""
pipeline/video_builder.py
Uses MoviePy and Pillow to build the final video file.
Avoids ImageMagick dependency by drawing captions programmatically using Pillow.
Supports vertical 9:16 Shorts and horizontal 16:9 long-form videos.
"""

import os
import logging
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
)
from pipeline.config import (
    OUTPUT_DIR, ASSETS_DIR, BRAND_DIR, FONTS_DIR,
    SHORT_WIDTH, SHORT_HEIGHT, SHORT_FPS, BGM_VOLUME,
    COLOR_DARK, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WHITE,
    SUBTITLE_FONT_SIZE, SUBTITLE_Y_POS
)
from pipeline.subtitle_writer import srt_to_moviepy_subtitles

logger = logging.getLogger(__name__)


def get_default_font(size: int) -> ImageFont.FreeTypeFont:
    """Load bundled font or fall back to system default."""
    font_path = FONTS_DIR / "Montserrat-Bold.ttf"
    if not font_path.exists():
        # Ensure directory exists and download a basic font if possible or use default
        FONTS_DIR.mkdir(parents=True, exist_ok=True)
        # Attempt to use a basic default font file
        try:
            return ImageFont.load_default()
        except Exception:
            pass
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception as e:
        logger.warning(f"Failed to load font {font_path}, using default. Error: {e}")
        return ImageFont.load_default()


def create_solid_background(width: int, height: int, duration: float, color: str = COLOR_DARK) -> ImageClip:
    """Create a static background image clip using MoviePy ColorClip."""
    # Convert hex to RGB list
    hex_color = color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # In MoviePy 2.x, ColorClip takes size and color parameters
    bg = ColorClip(size=(width, height), color=rgb, duration=duration)
    return bg


def overlay_subtitles_on_frame(img_array: np.ndarray, t: float, subtitles: list[dict], width: int, height: int) -> np.ndarray:
    """
    Renders subtitles onto a single frame (numpy array) using Pillow.
    This bypasses any ImageMagick binary requirements.
    """
    # Convert moviepy frame (numpy array) to Pillow Image
    img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(img)
    
    # Find active subtitle
    active_text = ""
    for sub in subtitles:
        if sub["start"] <= t <= sub["end"]:
            active_text = sub["text"]
            break
            
    if not active_text:
        return np.array(img)
        
    font = get_default_font(SUBTITLE_FONT_SIZE)
    
    # Wrap text if too long
    words = active_text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        # Measure line length
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w > width * 0.85:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    # Calculate starting Y coordinate
    total_height = 0
    line_sizes = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        line_sizes.append((line_w, line_h))
        total_height += line_h + 10
        
    start_y = int(height * SUBTITLE_Y_POS) - (total_height // 2)
    
    # Draw background box for readability
    padding = 15
    box_w = max(w for w, h in line_sizes) + (padding * 2)
    box_h = total_height + (padding * 2)
    box_x1 = (width - box_w) // 2
    box_y1 = start_y - padding
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + box_h
    
    # Draw semi-transparent black rectangle
    draw.rounded_rectangle(
        [box_x1, box_y1, box_x2, box_y2],
        radius=12,
        fill=(0, 0, 0, 180)
    )
    
    # Draw text lines
    current_y = start_y
    for i, line in enumerate(lines):
        line_w, line_h = line_sizes[i]
        x = (width - line_w) // 2
        
        # Stroke/Outline effect
        draw.text(
            (x, current_y), line, font=font, fill=COLOR_WHITE,
            stroke_width=2, stroke_fill=COLOR_DARK
        )
        current_y += line_h + 10
        
    return np.array(img)


def build_video(audio_path: Path, srt_path: Path, output_filename: str = "final_short.mp4", bg_color: str = COLOR_DARK, bg_video_path: Path = None) -> Path:
    """
    Combines background, voice audio, background music, and subtitles into a final video.
    """
    output_path = OUTPUT_DIR / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load voiceover audio
    voice_audio = AudioFileClip(str(audio_path))
    duration = voice_audio.duration
    
    # Set up background
    if bg_video_path and bg_video_path.exists():
        logger.info(f"Using video background: {bg_video_path}")
        bg = VideoFileClip(str(bg_video_path)).subclipped(0, duration)
        # Resize to fit target width/height
        bg = bg.resized(new_size=(SHORT_WIDTH, SHORT_HEIGHT))
    else:
        logger.info(f"Using color background: {bg_color}")
        bg = create_solid_background(SHORT_WIDTH, SHORT_HEIGHT, duration, bg_color)
        
    # Load background music (optional)
    bgm_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    final_audio = voice_audio
    
    if bgm_files:
        bgm_path = bgm_files[0]
        logger.info(f"Using background music: {bgm_path}")
        bgm = AudioFileClip(str(bgm_path))
        # Loop background music if it's shorter than video duration
        bgm = bgm.loop(duration=duration).with_volume_scaled(BGM_VOLUME)
        # Mix audio tracks
        from moviepy import CompositeAudioClip
        final_audio = CompositeAudioClip([voice_audio, bgm])
        
    # Assign audio to background
    video = bg.with_audio(final_audio)
    
    # Parse subtitles
    subtitles = srt_to_moviepy_subtitles(srt_path)
    
    # Apply subtitles via frames mapping function
    logger.info("Applying subtitles to video frames...")
    final_video = video.transform(
        lambda get_frame, t: overlay_subtitles_on_frame(get_frame(t), t, subtitles, SHORT_WIDTH, SHORT_HEIGHT)
    )
    
    # Render final output
    logger.info(f"Rendering final video to {output_path}...")
    final_video.write_videofile(
        str(output_path),
        fps=SHORT_FPS,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )
    
    # Close clips to free memory
    voice_audio.close()
    if bg_video_path and bg_video_path.exists():
        bg.close()
    final_video.close()
    
    logger.info(f"Video built successfully at: {output_path}")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Simple manual/local testing trigger
    # In practice, run this through pytest or CLI scripts
    print("Video builder loaded.")
