"""
tests/test_thumbnail_maker.py
Validates thumbnail generation dimensions and file integrity.
"""

from PIL import Image
from pipeline.config import OUTPUT_DIR
from pipeline.thumbnail_maker import generate_thumbnail


def test_generate_thumbnail(tmp_path):
    # Override OUTPUT_DIR in config or test generation
    # Since we can just specify a custom filename or check OUTPUT_DIR output
    output_filename = "test_thumb_output.jpg"
    target_path = OUTPUT_DIR / output_filename
    
    # Ensure it's clean
    if target_path.exists():
        target_path.unlink()
        
    p = generate_thumbnail("EASIEST CHATGPT HACK FOR STUDENTS", output_filename)
    
    assert p.exists()
    assert p.is_file()
    
    # Open and verify image specifications
    with Image.open(p) as img:
        assert img.size == (1280, 720)
        assert img.mode == "RGB"
        
    # Clean up test output
    if p.exists():
        p.unlink()
    
