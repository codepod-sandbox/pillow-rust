"""
Tests for ImageDraw arc, chord, and pieslice operations.

Tests adapted from upstream Pillow Tests/test_imagedraw.py:
  https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagedraw.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# arc
# ---------------------------------------------------------------------------

def test_arc_no_crash():
    """arc() should not crash for a standard call."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([10, 10, 90, 90], 0, 180)


def test_arc_with_color():
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([10, 10, 90, 90], 0, 90, fill=(255, 0, 0))
    # Some pixels on the arc should be red
    pixels = list(im.getdata())
    assert any(p[0] > 0 for p in pixels), "Expected red pixels on arc"


def test_arc_L_mode():
    im = Image.new("L", (100, 100), 0)
    draw = ImageDraw.Draw(im)
    draw.arc([10, 10, 90, 90], 0, 360, fill=200)
    pixels = list(im.getdata())
    assert any(p > 0 for p in pixels), "Expected non-zero pixels on arc"


def test_arc_full_circle():
    """360-degree arc — must not crash."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([5, 5, 45, 45], 0, 360, fill=(255, 255, 255))


def test_arc_default_color():
    """arc() without fill should default to white."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([5, 5, 45, 45], 0, 180)
    pixels = list(im.getdata())
    assert any(p != (0, 0, 0) for p in pixels)


def test_arc_tuple_coords():
    """arc() accepts [(x0,y0),(x1,y1)] style coordinates."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (45, 45)], 0, 180, fill=(0, 255, 0))


def test_arc_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        im = Image.new(mode, (50, 50))
        draw = ImageDraw.Draw(im)
        draw.arc([5, 5, 45, 45], 0, 90)
        assert im.mode == mode


# ---------------------------------------------------------------------------
# chord
# ---------------------------------------------------------------------------

def test_chord_no_crash():
    """chord() should not crash."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.chord([10, 10, 90, 90], 0, 180)


def test_chord_fill():
    """chord() fill should paint interior pixels."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.chord([20, 20, 80, 80], 0, 180, fill=(0, 255, 0))
    pixels = list(im.getdata())
    assert any(p[1] > 0 for p in pixels), "Expected green fill pixels"


def test_chord_outline():
    """chord() outline only should paint outline pixels."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.chord([20, 20, 80, 80], 0, 180, outline=(255, 0, 0))
    pixels = list(im.getdata())
    assert any(p[0] > 0 for p in pixels), "Expected red outline pixels"


def test_chord_fill_and_outline():
    """chord() fill + outline should not crash."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.chord([20, 20, 80, 80], 0, 180, fill=(0, 0, 255), outline=(255, 255, 0))
    pixels = list(im.getdata())
    assert any(p != (0, 0, 0) for p in pixels)


def test_chord_L_mode():
    im = Image.new("L", (100, 100), 0)
    draw = ImageDraw.Draw(im)
    draw.chord([10, 10, 90, 90], 0, 270, fill=200)
    pixels = list(im.getdata())
    assert any(p > 0 for p in pixels)


def test_chord_full_circle():
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.chord([5, 5, 45, 45], 0, 360, fill=(255, 255, 255))


# ---------------------------------------------------------------------------
# pieslice
# ---------------------------------------------------------------------------

def test_pieslice_no_crash():
    """pieslice() should not crash."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([10, 10, 90, 90], 0, 90)


def test_pieslice_fill():
    """pieslice() fill should paint interior pixels."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([20, 20, 80, 80], 0, 90, fill=(255, 128, 0))
    pixels = list(im.getdata())
    assert any(p[0] > 0 for p in pixels), "Expected orange fill pixels"


def test_pieslice_outline():
    """pieslice() outline only should paint outline pixels."""
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([20, 20, 80, 80], 0, 90, outline=(0, 200, 200))
    pixels = list(im.getdata())
    assert any(p != (0, 0, 0) for p in pixels)


def test_pieslice_fill_and_outline():
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([20, 20, 80, 80], 0, 270, fill=(0, 0, 255), outline=(255, 255, 255))
    pixels = list(im.getdata())
    assert any(p != (0, 0, 0) for p in pixels)


def test_pieslice_L_mode():
    im = Image.new("L", (100, 100), 0)
    draw = ImageDraw.Draw(im)
    draw.pieslice([10, 10, 90, 90], 45, 315, fill=150)
    pixels = list(im.getdata())
    assert any(p > 0 for p in pixels)


def test_pieslice_full_circle():
    """Full 360° pieslice should fill entire ellipse."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([0, 0, 50, 50], 0, 360, fill=(255, 255, 255))
    # Center pixel should be white
    assert im.getpixel((25, 25)) == (255, 255, 255)


def test_pieslice_tuple_coords():
    """pieslice() accepts [(x0,y0),(x1,y1)] style coordinates."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (45, 45)], 0, 90, fill=(255, 0, 0))


def test_pieslice_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        im = Image.new(mode, (50, 50))
        draw = ImageDraw.Draw(im)
        draw.pieslice([5, 5, 45, 45], 0, 180)
        assert im.mode == mode
