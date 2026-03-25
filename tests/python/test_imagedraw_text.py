"""Tests for ImageDraw text operations."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageFont


def _img(mode="RGB", size=(100, 50), color=(255, 255, 255)):
    return Image.new(mode, size, color)


# ---------------------------------------------------------------------------
# textbbox() — bounding box of text
# ---------------------------------------------------------------------------

def test_textbbox_returns_4_tuple():
    im = _img()
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), "Hello")
    assert len(bbox) == 4


def test_textbbox_positive_dimensions():
    im = _img()
    draw = ImageDraw.Draw(im)
    x0, y0, x1, y1 = draw.textbbox((0, 0), "Hello")
    assert x1 > x0
    assert y1 > y0


def test_textbbox_empty_string():
    im = _img()
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), "")
    # Empty string: width should be 0 or very small
    x0, y0, x1, y1 = bbox
    assert x1 - x0 == 0 or x1 - x0 < 5


def test_textbbox_longer_string_wider():
    im = _img()
    draw = ImageDraw.Draw(im)
    bbox_short = draw.textbbox((0, 0), "Hi")
    bbox_long = draw.textbbox((0, 0), "Hello World")
    # Longer string should have wider bounding box
    assert (bbox_long[2] - bbox_long[0]) > (bbox_short[2] - bbox_short[0])


def test_textbbox_position_offset():
    im = _img()
    draw = ImageDraw.Draw(im)
    bbox1 = draw.textbbox((0, 0), "Test")
    bbox2 = draw.textbbox((10, 20), "Test")
    # Offset the anchor, bbox should shift accordingly
    assert bbox2[0] >= bbox1[0]
    assert bbox2[1] >= bbox1[1]


# ---------------------------------------------------------------------------
# text() — draw text on image
# ---------------------------------------------------------------------------

def test_text_modifies_image():
    im = _img("RGB", (200, 50), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.text((5, 5), "Hi", fill=(0, 0, 0))
    # Some pixel should have changed from white (255,255,255) to something darker
    # Find at least one non-white pixel in the text area
    changed = False
    for x in range(5, 80):
        for y in range(5, 30):
            px = im.getpixel((x, y))
            if px != (255, 255, 255):
                changed = True
                break
        if changed:
            break
    assert changed, "Text should have drawn some pixels"


def test_text_L_mode():
    im = Image.new("L", (200, 50), 255)
    draw = ImageDraw.Draw(im)
    draw.text((5, 5), "Hi", fill=0)
    # Check some pixels changed to non-white
    changed = any(im.getpixel((x, y)) < 200 for x in range(5, 80) for y in range(5, 30))
    assert changed


def test_text_does_not_crash_empty():
    """Drawing empty string should not crash."""
    im = _img()
    draw = ImageDraw.Draw(im)
    draw.text((5, 5), "", fill=(0, 0, 0))


def test_text_multiline():
    """Multiline text (with \\n) should not crash."""
    im = _img("RGB", (200, 100))
    draw = ImageDraw.Draw(im)
    draw.text((5, 5), "Line 1\nLine 2", fill=(0, 0, 0))


# ---------------------------------------------------------------------------
# textlength()
# ---------------------------------------------------------------------------

def test_textlength_positive():
    im = _img()
    draw = ImageDraw.Draw(im)
    length = draw.textlength("Hello")
    assert length > 0


def test_textlength_empty_zero():
    im = _img()
    draw = ImageDraw.Draw(im)
    length = draw.textlength("")
    assert length == 0


def test_textlength_longer_string_longer():
    im = _img()
    draw = ImageDraw.Draw(im)
    l1 = draw.textlength("Hi")
    l2 = draw.textlength("Hello World")
    assert l2 > l1


# ---------------------------------------------------------------------------
# ImageFont interaction
# ---------------------------------------------------------------------------

def test_truetype_font_basic():
    """Load a TrueType font and draw text."""
    font_path = os.path.join(os.path.dirname(__file__),
                              "../../crates/pil-rust-core/src/fonts/LiberationSans-Regular.ttf")
    if not os.path.exists(font_path):
        pytest.skip("font file not found")
    font = ImageFont.truetype(font_path, size=16)
    im = _img("RGB", (200, 50), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.text((5, 5), "Hello", font=font, fill=(0, 0, 0))
    # At least some pixel should have changed
    changed = any(im.getpixel((x, 10)) != (255, 255, 255) for x in range(5, 100))
    assert changed


def test_truetype_textbbox():
    """TrueType font gives reasonable bounding box."""
    font_path = os.path.join(os.path.dirname(__file__),
                              "../../crates/pil-rust-core/src/fonts/LiberationSans-Regular.ttf")
    if not os.path.exists(font_path):
        pytest.skip("font file not found")
    font = ImageFont.truetype(font_path, size=20)
    im = _img()
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), "Hello", font=font)
    x0, y0, x1, y1 = bbox
    assert x1 > x0
    assert y1 > y0
    # Width should be reasonable for "Hello" at 20px
    assert (x1 - x0) > 20


if __name__ == "__main__":
    pytest.main()
