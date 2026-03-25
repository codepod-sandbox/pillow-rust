"""Tests for Image.paste() with out-of-bounds / edge positions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Paste at negative coordinates (partial paste)
# ---------------------------------------------------------------------------

def test_paste_negative_x():
    """Paste with negative x clips to visible area."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (6, 6), 200)
    base.paste(patch, (-3, 0))  # 3 columns outside left edge
    # Columns 0-2 should have paste value (from patch columns 3-5)
    assert base.getpixel((0, 0)) == 200
    assert base.getpixel((2, 0)) == 200
    # Column 3 onwards should be unchanged
    assert base.getpixel((3, 0)) == 0


def test_paste_negative_y():
    """Paste with negative y clips to visible area."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (6, 6), 200)
    base.paste(patch, (0, -3))  # 3 rows above top edge
    # Rows 0-2 should have paste value (from patch rows 3-5)
    assert base.getpixel((0, 0)) == 200
    assert base.getpixel((0, 2)) == 200
    # Row 3 onwards should be unchanged
    assert base.getpixel((0, 3)) == 0


def test_paste_beyond_right():
    """Paste extending beyond right edge clips to visible area."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (6, 6), 200)
    base.paste(patch, (7, 0))  # starts at x=7, extends to x=12 (out of bounds)
    # Columns 7-9 should have paste value (first 3 columns of patch)
    assert base.getpixel((7, 0)) == 200
    assert base.getpixel((9, 0)) == 200
    # Earlier columns unchanged
    assert base.getpixel((6, 0)) == 0


def test_paste_beyond_bottom():
    """Paste extending beyond bottom edge clips to visible area."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (6, 6), 200)
    base.paste(patch, (0, 7))  # starts at y=7, extends to y=12 (out of bounds)
    assert base.getpixel((0, 7)) == 200
    assert base.getpixel((0, 9)) == 200
    assert base.getpixel((0, 6)) == 0


def test_paste_fully_outside():
    """Paste completely outside should not modify image."""
    base = Image.new("L", (10, 10), 50)
    patch = Image.new("L", (4, 4), 200)
    base.paste(patch, (20, 20))
    assert base.getpixel((5, 5)) == 50
    assert base.getpixel((0, 0)) == 50


def test_paste_negative_both():
    """Paste starting at negative (x, y) — only overlap region visible."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (8, 8), 200)
    base.paste(patch, (-4, -4))
    # Only bottom-right 4x4 of patch is visible at (0,0)-(3,3)
    assert base.getpixel((0, 0)) == 200
    assert base.getpixel((3, 3)) == 200
    assert base.getpixel((4, 4)) == 0


# ---------------------------------------------------------------------------
# Paste at exact corner positions
# ---------------------------------------------------------------------------

def test_paste_top_left_corner():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 200)
    base.paste(patch, (0, 0))
    assert base.getpixel((0, 0)) == 200
    assert base.getpixel((2, 2)) == 200
    assert base.getpixel((3, 0)) == 0


def test_paste_bottom_right_corner():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 200)
    base.paste(patch, (7, 7))
    assert base.getpixel((7, 7)) == 200
    assert base.getpixel((9, 9)) == 200
    assert base.getpixel((6, 6)) == 0


def test_paste_top_right_corner():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 200)
    base.paste(patch, (7, 0))
    assert base.getpixel((7, 0)) == 200
    assert base.getpixel((9, 2)) == 200
    assert base.getpixel((6, 0)) == 0


def test_paste_bottom_left_corner():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 200)
    base.paste(patch, (0, 7))
    assert base.getpixel((0, 7)) == 200
    assert base.getpixel((2, 9)) == 200
    assert base.getpixel((0, 6)) == 0


# ---------------------------------------------------------------------------
# Paste full image
# ---------------------------------------------------------------------------

def test_paste_full_image():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (10, 10), 200)
    base.paste(patch, (0, 0))
    assert base.getpixel((0, 0)) == 200
    assert base.getpixel((9, 9)) == 200


if __name__ == "__main__":
    pytest.main()
