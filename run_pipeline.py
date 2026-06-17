"""
run_pipeline.py
Main entry point for executing the automated content generation and upload.
Coordinates the entire flow: topic selection, scriptwriting, voice synthesis,
subtitle generation, rendering, thumbnail creation, and YouTube upload.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logger first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("pipeline")

# Import pipeline steps
from pipeline.config import UPLOAD_VIDEO, DRY_RUN, OUTPUT_DIR
from pipeline.topic_generator import get_next_topic
from pipeline.script_writer import generate_script
from pipeline.tts_engine import synthesize
from pipeline.subtitle_writer import generate_srt
from pipeline.video_builder import build_video
from pipeline.thumbnail_maker import generate_thumbnail
from pipeline.youtube_uploader import upload_video


def run(upload: bool = None, dry_run: bool = None):
    # Overwrite configs if args provided
    do_upload = upload if upload is not None else UPLOAD_VIDEO
    is_dry_run = dry_run if dry_run is not None else DRY_RUN

    logger.info("==========================================")
    logger.info("  Starting Automated YouTube pipeline     ")
    logger.info(f"  Upload: {do_upload} | Dry Run: {is_dry_run} ")
    logger.info("==========================================")

    # 0. Clean workspace
    if OUTPUT_DIR.exists():
        for file in OUTPUT_DIR.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete temp file {file}: {e}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Topic selection
    try:
        topic = get_next_topic()
        logger.info(f"[Step 1] Topic loaded: {topic['topic']}")
    except Exception as e:
        logger.error(f"Failed in Topic Selection: {e}")
        sys.exit(1)

    # 2. Scriptwriting
    try:
        script = generate_script(topic)
        logger.info("[Step 2] Script generated successfully.")
        logger.info(f"Script title: {script['title']}")
        logger.info(f"Thumbnail text: {script['thumbnail_text']}")
    except Exception as e:
        logger.error(f"Failed in Script Writing: {e}")
        sys.exit(1)

    # 3. Audio / TTS Synthesis
    try:
        logger.info("[Step 3] Starting Text-to-Speech synthesis...")
        audio_path, duration = synthesize(script["narration"], "voiceover.mp3")
        logger.info(f"Synthesized voiceover. Duration: {duration:.2f}s")
    except Exception as e:
        logger.error(f"Failed in Text-to-Speech: {e}")
        sys.exit(1)

    # 4. Caption timing file (.srt)
    try:
        logger.info("[Step 4] Generating subtitle timing...")
        srt_path = generate_srt(script["narration"], duration, "subtitles.srt")
    except Exception as e:
        logger.error(f"Failed in Subtitle generation: {e}")
        sys.exit(1)

    # 5. Thumbnail Generation
    try:
        logger.info("[Step 5] Generating custom thumbnail image...")
        thumbnail_path = generate_thumbnail(script["thumbnail_text"], "thumbnail.jpg")
    except Exception as e:
        logger.error(f"Failed in Thumbnail creation: {e}")
        sys.exit(1)

    # 6. Video assembly & Rendering
    try:
        logger.info("[Step 6] Compiling assets into video file...")
        # Optional: check if B-roll loop exists, otherwise falls back to solid color background
        video_path = build_video(
            audio_path=audio_path,
            srt_path=srt_path,
            output_filename="shorts_video.mp4"
        )
    except Exception as e:
        logger.error(f"Failed in Video compilation/rendering: {e}")
        sys.exit(1)

    # 7. YouTube Upload
    if do_upload:
        try:
            logger.info("[Step 7] Uploading video to YouTube...")
            video_id = upload_video(
                video_path=video_path,
                metadata=script,
                thumbnail_path=thumbnail_path,
                srt_path=srt_path
            )
            logger.info(f"Video uploaded successfully. Video ID: {video_id}")
            logger.info(f"Live URL: https://youtu.be/{video_id}")
        except Exception as e:
            logger.error(f"Failed in YouTube Upload: {e}")
            sys.exit(1)
    else:
        logger.info("[Step 7] Upload skipped (UPLOAD_VIDEO=false or DRY_RUN=true)")

    logger.info("==========================================")
    logger.info("  Pipeline Executed Successfully!         ")
    logger.info("==========================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated YouTube Channel Pipeline Controller")
    parser.add_argument("--upload", type=str, choices=["true", "false"], help="Override config upload flag")
    parser.add_argument("--dry-run", type=str, choices=["true", "false"], help="Override config dry-run flag")
    args = parser.parse_args()

    upload_override = None
    if args.upload:
        upload_override = args.upload.lower() == "true"

    dry_run_override = None
    if args.dry_run:
        dry_run_override = args.dry_run.lower() == "true"

    run(upload=upload_override, dry_run=dry_run_override)
