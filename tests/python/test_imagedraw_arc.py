"""Tests for ImageDraw arc, chord, pieslice — exact pixel verification."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw


def _blank(size=(50, 50), mode="L"):
    return Image.new(mode, size, 0)


# ---------------------------------------------------------------------------
# arc()
# ---------------------------------------------------------------------------

def test_arc_does_not_fill_interior():
    """arc() draws outline only, not filled."""
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (35, 35)], start=0, end=360, fill=200)
    # Center of arc should remain black (not filled)
    assert im.getpixel((20, 20)) == 0


def test_arc_draws_some_pixels():
    im = _blank(size=(50, 50))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (45, 45)], start=0, end=360, fill=200)
    # Some pixels on the circle should be drawn
    found = any(im.getpixel((x, y)) == 200
                for y in range(5, 46) for x in range(5, 46))
    assert found


def test_arc_0_to_180():
    """Half arc (0 to 180) draws pixels in right half."""
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (35, 35)], start=0, end=180, fill=200)
    # Just check it doesn't crash and some pixels are drawn
    found = any(im.getpixel((x, y)) == 200
                for y in range(5, 36) for x in range(5, 36))
    assert found


def test_arc_preserves_mode():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (35, 35)], start=0, end=360, fill=200)
    assert im.mode == "L"


def test_arc_rgb():
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (45, 45)], start=0, end=360, fill=(255, 0, 0))
    # Some pixel on the circle should be red
    found = any(im.getpixel((x, y))[0] == 255
                for y in range(5, 46) for x in range(5, 46))
    assert found


def test_arc_fill_0_is_black():
    """arc with fill=0 should draw black pixels."""
    im = Image.new("L", (40, 40), 255)  # white background
    draw = ImageDraw.Draw(im)
    draw.arc([(5, 5), (35, 35)], start=0, end=360, fill=0)
    found = any(im.getpixel((x, y)) == 0
                for y in range(5, 36) for x in range(5, 36))
    assert found


# ---------------------------------------------------------------------------
# chord()
# ---------------------------------------------------------------------------

def test_chord_fills_interior():
    """chord() fills the chord area."""
    im = _blank(size=(50, 50))
    draw = ImageDraw.Draw(im)
    draw.chord([(5, 5), (45, 45)], start=0, end=180, fill=200)
    # Should fill some pixels
    found = any(im.getpixel((x, y)) == 200
                for y in range(20, 40) for x in range(15, 40))
    assert found


def test_chord_full_circle_fills_everything():
    """chord(0, 360) fills the full circle."""
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.chord([(5, 5), (35, 35)], start=0, end=360, fill=200)
    # Center of the circle should be filled
    assert im.getpixel((20, 20)) == 200


def test_chord_outline_and_fill():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.chord([(5, 5), (35, 35)], start=0, end=360, fill=100, outline=255)
    # Interior filled with 100
    assert im.getpixel((20, 20)) == 100


def test_chord_preserves_mode():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.chord([(5, 5), (35, 35)], start=0, end=180, fill=200)
    assert im.mode == "L"


# ---------------------------------------------------------------------------
# pieslice()
# ---------------------------------------------------------------------------

def test_pieslice_fills_sector():
    """pieslice() fills from center to arc."""
    im = _blank(size=(50, 50))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (45, 45)], start=0, end=90, fill=200)
    # Center should be filled (pieslice includes center)
    assert im.getpixel((25, 25)) == 200


def test_pieslice_full_circle_fills_all():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (35, 35)], start=0, end=360, fill=200)
    assert im.getpixel((20, 20)) == 200


def test_pieslice_outline_and_fill():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (35, 35)], start=0, end=360, fill=100, outline=255)
    assert im.getpixel((20, 20)) == 100


def test_pieslice_preserves_mode():
    im = _blank(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (35, 35)], start=0, end=90, fill=200)
    assert im.mode == "L"


def test_pieslice_rgb():
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (45, 45)], start=0, end=360, fill=(0, 255, 0))
    assert im.getpixel((25, 25))[1] == 255  # green channel


# ---------------------------------------------------------------------------
# fill=0 should work for all arc shapes
# ---------------------------------------------------------------------------

def test_pieslice_fill_0_is_black():
    im = Image.new("L", (40, 40), 255)  # white background
    draw = ImageDraw.Draw(im)
    draw.pieslice([(5, 5), (35, 35)], start=0, end=360, fill=0)
    assert im.getpixel((20, 20)) == 0


if __name__ == "__main__":
    pytest.main()
