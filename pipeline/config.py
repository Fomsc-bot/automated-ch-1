"""
pipeline/config.py
Central configuration for the AI Life Hacks YouTube Channel pipeline.
All tunable parameters live here — change once, affects the entire pipeline.
"""

import os
from pathlib import Path

# ─── Directory paths ──────────────────────────────────────────────────────────
ROOT_DIR        = Path(__file__).parent.parent
ASSETS_DIR      = ROOT_DIR / "assets"
TOPICS_DIR      = ROOT_DIR / "topics"
LOGS_DIR        = ROOT_DIR / "logs"
OUTPUT_DIR      = ROOT_DIR / "output"          # Temp build artifacts

FONTS_DIR       = ASSETS_DIR / "fonts"
MUSIC_DIR       = ASSETS_DIR / "music"
BRAND_DIR       = ASSETS_DIR / "brand"
TEMPLATES_DIR   = ASSETS_DIR / "templates"

TOPIC_POOL_FILE = TOPICS_DIR / "topic_pool.json"
USED_TOPICS_FILE= TOPICS_DIR / "used_topics.json"
UPLOAD_LOG_FILE = LOGS_DIR   / "upload_log.json"

# ─── Video specs ──────────────────────────────────────────────────────────────
SHORT_WIDTH     = 1080
SHORT_HEIGHT    = 1920
SHORT_FPS       = 30
SHORT_MAX_SECS  = 58          # Keep under 60s hard limit

LONG_WIDTH      = 1920
LONG_HEIGHT     = 1080
LONG_FPS        = 30
LONG_TARGET_MIN = 8           # Minimum long-video length in minutes

THUMBNAIL_WIDTH  = 1280
THUMBNAIL_HEIGHT = 720

# ─── Brand colours (hex) ──────────────────────────────────────────────────────
COLOR_PRIMARY    = "#00D4FF"   # Electric cyan
COLOR_DARK       = "#0A0A0A"   # Deep black background
COLOR_ACCENT     = "#FFD600"   # Highlight yellow
COLOR_WHITE      = "#FFFFFF"
COLOR_SUBTITLE_BG= "#000000"   # Semi-transparent subtitle box

# ─── TTS settings ─────────────────────────────────────────────────────────────
TTS_PROVIDER     = os.getenv("TTS_PROVIDER", "google")   # "google" | "elevenlabs"
GOOGLE_TTS_VOICE = "en-US-Wavenet-F"                     # Female WaveNet voice
GOOGLE_TTS_LANG  = "en-US"
ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"             # Adam — change as needed
ELEVENLABS_MODEL    = "eleven_flash_v2_5"

# ─── OpenAI settings ──────────────────────────────────────────────────────────
OPENAI_MODEL        = "gpt-4o-mini"     # Cost-efficient; swap to gpt-4o for quality
OPENAI_TEMPERATURE  = 0.82
SCRIPT_MAX_WORDS    = 145               # ~45 seconds at avg speaking pace

# ─── YouTube upload settings ─────────────────────────────────────────────────
YT_CATEGORY_ID  = "28"         # Science & Technology
YT_PRIVACY      = "public"     # "public" | "private" | "unlisted"
YT_MADE_FOR_KIDS= False
YT_DEFAULT_LANG = "en"
YT_SHORTS_TAG   = "#Shorts"

# ─── Content pipeline flags ───────────────────────────────────────────────────
VIDEO_TYPE      = os.getenv("VIDEO_TYPE", "short")   # "short" | "long"
DRY_RUN         = os.getenv("DRY_RUN", "false").lower() == "true"
UPLOAD_VIDEO    = os.getenv("UPLOAD_VIDEO", "true").lower() == "true"

# ─── BGM volume ───────────────────────────────────────────────────────────────
BGM_VOLUME      = 0.10          # 10% — never drown the voice

# ─── Subtitle style ───────────────────────────────────────────────────────────
SUBTITLE_FONT_SIZE  = 52
SUBTITLE_COLOR      = "white"
SUBTITLE_STROKE_CLR = "black"
SUBTITLE_STROKE_W   = 2
SUBTITLE_Y_POS      = 0.78      # 78% down the frame
