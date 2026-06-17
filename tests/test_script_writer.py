"""
tests/test_script_writer.py
Validates the script writer outputs a conforming dictionary with correct keys.
"""

import os
from unittest.mock import MagicMock, patch
from pipeline.script_writer import generate_script


@patch("pipeline.script_writer.requests.post")
def test_generate_script(mock_post):
    # Mock environment variable
    os.environ["GEMINI_API_KEY"] = "mock_api_key"

    # Setup mock requests response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """{
                                "narration": "Did you know you can summarize a PDF in seconds? Open ChatGPT and upload it. Done!",
                                "scenes": ["Struggling student", "AI summarizing", "Happy student"],
                                "title": "Instantly Summarize PDFs with AI! 🤖 #Shorts",
                                "description": "Short summary of PDF capabilities with AI.",
                                "tags": ["AI", "productivity", "ChatGPT"],
                                "thumbnail_text": "Summarize PDFs Instantly",
                                "hook": "Did you know you can summarize a PDF in seconds?",
                                "variant": "A"
                            }"""
                        }
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    sample_topic = {
        "id": 2,
        "topic": "Summarize any PDF instantly with AI",
        "ai_tool": "ChatGPT",
        "category": "research",
        "variant": "A"
    }

    result = generate_script(sample_topic)

    assert result["variant"] == "A"
    assert "narration" in result
    assert "scenes" in result
    assert len(result["tags"]) == 3
    assert result["thumbnail_text"] == "Summarize PDFs Instantly"
    mock_post.assert_called_once()

