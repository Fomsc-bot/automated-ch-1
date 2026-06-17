"""
pipeline/youtube_uploader.py
Uses YouTube Data API v3 to upload the generated video, thumbnail, and captions.
Uses OAuth2 refresh token flow to work headlessly in GitHub Actions.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from pipeline.config import (
    UPLOAD_LOG_FILE, YT_CATEGORY_ID, YT_PRIVACY, YT_MADE_FOR_KIDS,
    YT_DEFAULT_LANG, DRY_RUN
)

logger = logging.getLogger(__name__)


def _get_youtube_client() -> build:
    """Reconstructs credentials from env vars and builds the YouTube API client."""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        # Fallback to local token.json if available
        token_path = Path("token.json")
        client_secret_path = Path("client_secret.json")
        
        if token_path.exists() and client_secret_path.exists():
            logger.info("Loading YouTube credentials from local token.json and client_secret.json")
            with open(token_path, "r") as f:
                token_data = json.load(f)
            with open(client_secret_path, "r") as f:
                secret_data = json.load(f)
            
            # Extract client info
            web_or_installed = "installed" if "installed" in secret_data else "web"
            client_id = secret_data[web_or_installed]["client_id"]
            client_secret = secret_data[web_or_installed]["client_secret"]
            refresh_token = token_data.get("refresh_token")
        else:
            raise EnvironmentError(
                "Missing YouTube API secrets: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN "
                "must be configured in environment variables or client_secret.json/token.json must exist."
            )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    # Refresh token if expired
    if creds.expired or not creds.valid:
        logger.info("Refreshing OAuth2 access token...")
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: Path, metadata: dict, thumbnail_path: Path = None, srt_path: Path = None) -> str:
    """
    Uploads video to YouTube with metadata, custom thumbnail, and captions.

    Args:
        video_path: Path to MP4 video
        metadata: Dict containing: title, description, tags
        thumbnail_path: Path to custom thumbnail JPEG (optional)
        srt_path: Path to captions file (optional)

    Returns:
        YouTube Video ID (string)
    """
    if DRY_RUN:
        logger.info("[DRY RUN] Bypassing upload_video. Mocking successful upload.")
        return "mock_video_id_12345"

    youtube = _get_youtube_client()

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": YT_CATEGORY_ID,
            "defaultLanguage": YT_DEFAULT_LANG
        },
        "status": {
            "privacyStatus": YT_PRIVACY,
            "selfDeclaredMadeForKids": YT_MADE_FOR_KIDS
        }
    }

    # Upload video media file
    media = MediaFileUpload(
        str(video_path),
        chunksize=1024 * 1024,
        resumable=True,
        mimetype="video/mp4"
    )

    logger.info(f"Starting YouTube video upload: {video_path.name}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Execute resumable upload
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Uploading video... {int(status.progress() * 100)}% complete")

    video_id = response["id"]
    video_url = f"https://youtu.be/{video_id}"
    logger.info(f"Video uploaded successfully. Video ID: {video_id} | URL: {video_url}")

    # Set Custom Thumbnail (optional)
    if thumbnail_path and thumbnail_path.exists():
        logger.info(f"Uploading thumbnail: {thumbnail_path.name}")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
            ).execute()
            logger.info("Thumbnail set successfully.")
        except Exception as e:
            logger.error(f"Failed to set custom thumbnail: {e}")

    # Set Captions/SRT (optional)
    if srt_path and srt_path.exists():
        logger.info(f"Uploading subtitles: {srt_path.name}")
        try:
            youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": YT_DEFAULT_LANG,
                        "name": "English Captions",
                        "isDraft": False
                    }
                },
                media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream")
            ).execute()
            logger.info("Subtitles uploaded successfully.")
        except Exception as e:
            logger.error(f"Failed to upload subtitles: {e}")

    # Log results
    _log_upload(video_id, metadata["title"], video_url)

    return video_id


def _log_upload(video_id: str, title: str, url: str) -> None:
    """Append upload details to local log file."""
    log_data = []
    if UPLOAD_LOG_FILE.exists():
        try:
            with open(UPLOAD_LOG_FILE, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception:
            pass

    log_data.append({
        "timestamp": datetime.now().isoformat(),
        "video_id": video_id,
        "title": title,
        "url": url
    })

    UPLOAD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(UPLOAD_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Simple syntax check
    print("YouTube Uploader module ready.")
