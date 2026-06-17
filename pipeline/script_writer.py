"""
pipeline/script_writer.py
Uses GPT-4o to generate a complete Short script + all YouTube metadata.

Output dict keys:
  narration       - Full voiceover text (≤145 words)
  scenes          - List of scene descriptions for video builder
  title           - SEO-optimised YouTube title (≤60 chars)
  description     - Full video description with hashtags
  tags            - List of 10 YouTube tags
  thumbnail_text  - Bold text for thumbnail (≤6 words)
  hook            - First sentence only (for A/B variant tracking)
  variant         - A | B | C
"""

import json
import logging
from openai import OpenAI

from pipeline.config import (
    OPENAI_MODEL, OPENAI_TEMPERATURE, SCRIPT_MAX_WORDS, YT_SHORTS_TAG
)

logger = logging.getLogger(__name__)

# ─── Prompt variants ──────────────────────────────────────────────────────────
VARIANT_INSTRUCTIONS = {
    "A": (
        "Story style: Start with a relatable problem (someone overwhelmed), "
        "then show an AI solution appearing like magic. Use warm, conversational tone. "
        "End with 'Subscribe for one AI hack every day!'"
    ),
    "B": (
        "Data-driven list style: Present exactly 3 numbered micro-steps to accomplish the task "
        "with AI. Use crisp, direct language with power words. "
        "End with 'Follow for daily AI productivity hacks!'"
    ),
    "C": (
        "Authority style: Speak as a confident AI productivity expert giving insider advice. "
        "Use slightly formal but energetic tone. Include one surprising fact or stat. "
        "End with 'Like and subscribe — new AI hack every day!'"
    ),
}

SYSTEM_PROMPT = """You are a world-class YouTube Shorts scriptwriter specialising in AI productivity content.
Your scripts go viral because they are punchy, specific, and immediately useful.
You always write in plain spoken English — no jargon, no fluff.
Return ONLY a valid JSON object with the exact keys requested. No markdown, no extra commentary."""


def _build_user_prompt(topic: dict) -> str:
    variant = topic.get("variant", "A")
    style   = VARIANT_INSTRUCTIONS.get(variant, VARIANT_INSTRUCTIONS["A"])
    ai_tool = topic.get("ai_tool", "ChatGPT")

    return f"""
Write a complete YouTube Shorts script package for this topic:
TOPIC: "{topic['topic']}"
AI TOOL FEATURED: {ai_tool}
STYLE: {style}

Return a JSON object with these exact keys:
{{
  "narration": "<Full voiceover narration, MAXIMUM {SCRIPT_MAX_WORDS} words, zero filler words>",
  "scenes": [
    "<Scene 1 description for animator — what appears on screen, max 15 words>",
    "<Scene 2 description>",
    "<Scene 3 description>",
    "<Scene 4 description>"
  ],
  "title": "<YouTube title ≤60 chars, include primary keyword + emoji, ends with {YT_SHORTS_TAG}>",
  "description": "<150-word description with: 1) topic summary 2) 3 actionable tips 3) subscribe CTA 4) these hashtags: #Shorts #AI #{ai_tool.replace(' ','')} #ProductivityHacks #AILifeHacks #AITips #LearnAI #ChatGPT #TechHacks #DigitalProductivity>",
  "tags": ["<tag1>","<tag2>","<tag3>","<tag4>","<tag5>","<tag6>","<tag7>","<tag8>","<tag9>","<tag10>"],
  "thumbnail_text": "<Bold thumbnail text ≤6 words — punchy, curiosity-driven>",
  "hook": "<First 1-2 sentences of narration only>",
  "variant": "{variant}"
}}
"""


def generate_script(topic: dict) -> dict:
    """
    Generates the complete script + metadata package for one video.

    Args:
        topic: dict from topic_generator.get_next_topic()

    Returns:
        dict with keys: narration, scenes, title, description, tags,
                        thumbnail_text, hook, variant
    """
    client = OpenAI()
    prompt = _build_user_prompt(topic)

    logger.info(f"Generating script for: {topic['topic']} (variant {topic.get('variant','A')})")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )

    raw = response.choices[0].message.content
    script = json.loads(raw)

    # Validate required keys
    required = {"narration", "scenes", "title", "description", "tags", "thumbnail_text", "hook", "variant"}
    missing  = required - set(script.keys())
    if missing:
        raise ValueError(f"GPT response missing keys: {missing}\nRaw: {raw}")

    # Enforce title length
    if len(script["title"]) > 100:
        script["title"] = script["title"][:97] + "..."

    logger.info(f"Script generated — title: {script['title']}")
    logger.info(f"Narration word count: {len(script['narration'].split())}")

    return script


if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO)

    sample_topic = {
        "id": 1,
        "topic": "Use ChatGPT to write a professional email in 30 seconds",
        "ai_tool": "ChatGPT",
        "category": "communication",
        "variant": "A",
    }
    result = generate_script(sample_topic)
    print(json.dumps(result, indent=2))
