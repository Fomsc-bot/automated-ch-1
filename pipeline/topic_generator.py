"""
pipeline/topic_generator.py
Selects the next unused topic from the pool, or generates a fresh one via GPT-4o.
Tracks state in topics/used_topics.json (committed back to repo after each run).
"""

import json
import random
import logging
from datetime import date
from pathlib import Path
import requests

from pipeline.config import (
    TOPIC_POOL_FILE, USED_TOPICS_FILE
)

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> dict | list:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_topic_via_gemini() -> dict:
    """Fallback: ask Gemini to invent a fresh topic when the pool is exhausted."""
    logger.info("Topic pool exhausted — generating new topic via Gemini")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is missing.")

    prompt = (
        "Generate ONE unique, highly shareable YouTube Shorts topic about using an AI tool "
        "(ChatGPT, Gemini, Claude, Perplexity, Midjourney, GitHub Copilot, etc.) to solve "
        "a real everyday problem. Format your response as JSON with keys: "
        "topic (string, ≤12 words), ai_tool (string), category (string), variant (A|B|C). "
        "Make it specific, punchy, and actionable. Return only the JSON object."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error ({response.status_code}): {response.text}")
        
    resp_json = response.json()
    try:
        raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Failed to parse Gemini topic response: {resp_json}")
        
    data = json.loads(raw_text)
    data["id"] = f"gemini-{date.today().isoformat()}"
    return data



def get_next_topic() -> dict:
    """
    Returns the next topic dict:
      {id, topic, ai_tool, category, variant}

    Priority:
      1. Unused topic from topic_pool.json (random selection within category rotation)
      2. GPT-4o generated topic (fallback)
    """
    pool_data = _load_json(TOPIC_POOL_FILE)
    all_topics: list[dict] = pool_data.get("topics", [])

    used_data: dict = _load_json(USED_TOPICS_FILE) if USED_TOPICS_FILE.exists() else {}
    used_ids: set = set(used_data.get("used_ids", []))

    # Filter unused topics
    available = [t for t in all_topics if str(t["id"]) not in used_ids]

    if not available:
        # Reset cycle — start over (or extend pool via GPT)
        logger.warning("All pool topics used — resetting cycle.")
        used_ids = set()
        available = all_topics

    if available:
        # Prefer balanced category rotation
        used_categories = used_data.get("recent_categories", [])
        least_used = [t for t in available if t["category"] not in used_categories[-5:]]
        topic = random.choice(least_used if least_used else available)
    else:
        topic = _generate_topic_via_gemini()

    # Update state
    used_ids.add(str(topic["id"]))
    recent_cats = used_data.get("recent_categories", [])
    recent_cats.append(topic["category"])
    recent_cats = recent_cats[-20:]  # Keep last 20

    _save_json(USED_TOPICS_FILE, {
        "used_ids":          list(used_ids),
        "recent_categories": recent_cats,
        "last_topic":        topic,
        "last_run":          date.today().isoformat(),
    })

    logger.info(f"Selected topic: {topic['topic']} (id={topic['id']})")
    return topic


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    t = get_next_topic()
    print(json.dumps(t, indent=2))
