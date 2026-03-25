"""Tests for Image.paste() edge cases: negative coords, out-of-bounds, mode interaction."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Negative coordinates
# ---------------------------------------------------------------------------

def test_paste_negative_x():
    """Paste at negative x should only show the part that overlaps."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (6, 6), (255, 0, 0))
    dst.paste(src, (-3, 0))
    # The right 3 columns of src (x=3..5) land at dst x=0..2
    assert dst.getpixel((0, 0)) == (255, 0, 0)
    assert dst.getpixel((1, 0)) == (255, 0, 0)
    assert dst.getpixel((2, 0)) == (255, 0, 0)
    # Beyond that is still black
    assert dst.getpixel((3, 0)) == (0, 0, 0)


def test_paste_negative_y():
    """Paste at negative y should only show the part that overlaps."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (6, 6), (0, 255, 0))
    dst.paste(src, (0, -2))
    # Rows 2..5 of src land at dst rows 0..3
    assert dst.getpixel((0, 0)) == (0, 255, 0)
    assert dst.getpixel((0, 3)) == (0, 255, 0)
    # Row 4 and beyond is still black
    assert dst.getpixel((0, 4)) == (0, 0, 0)


def test_paste_negative_both():
    """Paste at negative x and y."""
    dst = Image.new("L", (10, 10), 0)
    src = Image.new("L", (8, 8), 200)
    dst.paste(src, (-4, -4))
    # The bottom-right 4x4 of src (x=4..7, y=4..7) lands at dst (0,0)..(3,3)
    assert dst.getpixel((0, 0)) == 200
    assert dst.getpixel((3, 3)) == 200
    assert dst.getpixel((4, 0)) == 0  # outside paste region


def test_paste_fully_negative():
    """Paste entirely outside (negative) should be a no-op."""
    dst = Image.new("RGB", (10, 10), (255, 0, 0))
    src = Image.new("RGB", (5, 5), (0, 0, 255))
    dst.paste(src, (-10, -10))
    assert dst.getpixel((0, 0)) == (255, 0, 0)


# ---------------------------------------------------------------------------
# Out-of-bounds (positive)
# ---------------------------------------------------------------------------

def test_paste_beyond_right():
    """Paste that extends beyond right edge should be clipped."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (6, 4), (0, 0, 255))
    dst.paste(src, (7, 0))
    # x=7,8,9 should be pasted (first 3 cols of src)
    assert dst.getpixel((7, 0)) == (0, 0, 255)
    assert dst.getpixel((8, 0)) == (0, 0, 255)
    assert dst.getpixel((9, 0)) == (0, 0, 255)


def test_paste_fully_outside():
    """Paste entirely outside the destination — no-op."""
    dst = Image.new("L", (10, 10), 100)
    src = Image.new("L", (5, 5), 200)
    dst.paste(src, (20, 20))
    assert dst.getpixel((5, 5)) == 100  # unchanged


# ---------------------------------------------------------------------------
# Destination size unchanged
# ---------------------------------------------------------------------------

def test_paste_does_not_change_size():
    """Pasting should never change the destination image size."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (20, 20), (255, 255, 255))
    dst.paste(src, (-5, -5))
    assert dst.size == (10, 10)


# ---------------------------------------------------------------------------
# Mode compatibility: L into RGB and vice versa
# ---------------------------------------------------------------------------

def test_paste_L_into_L():
    dst = Image.new("L", (10, 10), 0)
    src = Image.new("L", (5, 5), 128)
    dst.paste(src, (0, 0))
    assert dst.getpixel((2, 2)) == 128


def test_paste_RGB_into_RGB():
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (100, 150, 200))
    dst.paste(src, (2, 2))
    assert dst.getpixel((4, 4)) == (100, 150, 200)
    assert dst.getpixel((0, 0)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# Mask-based paste
# ---------------------------------------------------------------------------

def test_paste_with_black_mask_no_change():
    """Black mask means nothing is pasted."""
    dst = Image.new("RGB", (10, 10), (100, 100, 100))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    mask = Image.new("L", (5, 5), 0)
    dst.paste(src, (0, 0), mask)
    assert dst.getpixel((2, 2)) == (100, 100, 100)


def test_paste_with_white_mask_full_paste():
    """White mask means full paste."""
    dst = Image.new("RGB", (10, 10), (100, 100, 100))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    mask = Image.new("L", (5, 5), 255)
    dst.paste(src, (0, 0), mask)
    assert dst.getpixel((2, 2)) == (255, 0, 0)


if __name__ == "__main__":
    pytest.main()
