"""
tests/test_script_writer.py
Validates the script writer outputs a conforming dictionary with correct keys.
"""

from unittest.mock import MagicMock, patch
from pipeline.script_writer import generate_script


@patch("pipeline.script_writer.OpenAI")
def test_generate_script(mock_openai_class):
    # Setup mock OpenAI response
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_chat = MagicMock()
    mock_client.chat = mock_chat
    
    mock_completions = MagicMock()
    mock_chat.completions = mock_completions
    
    # Expected GPT response payload
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="""{
            "narration": "Did you know you can summarize a PDF in seconds? Open ChatGPT and upload it. Done!",
            "scenes": ["Struggling student", "AI summarizing", "Happy student"],
            "title": "Instantly Summarize PDFs with AI! 🤖 #Shorts",
            "description": "Short summary of PDF capabilities with AI.",
            "tags": ["AI", "productivity", "ChatGPT"],
            "thumbnail_text": "Summarize PDFs Instantly",
            "hook": "Did you know you can summarize a PDF in seconds?",
            "variant": "A"
        }"""))
    ]
    mock_completions.create.return_value = mock_response
    
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
    mock_completions.create.assert_called_once()
