"""Tests for Image.crop() with out-of-bounds coordinates."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Crop with negative coordinates (extension outside image)
# ---------------------------------------------------------------------------

def test_crop_negative_x0():
    """Cropping with negative x0 should pad with zeros."""
    im = Image.new("L", (10, 10), 128)
    out = im.crop((-5, 0, 5, 5))
    assert out.size == (10, 5)
    # Left side (outside image) should be 0
    assert out.getpixel((0, 0)) == 0
    # Right side (inside image) should be 128
    assert out.getpixel((9, 0)) == 128


def test_crop_negative_y0():
    """Cropping with negative y0 should pad with zeros."""
    im = Image.new("L", (10, 10), 128)
    out = im.crop((0, -5, 10, 5))
    assert out.size == (10, 10)
    # Top part (outside) should be 0
    assert out.getpixel((5, 0)) == 0
    # Bottom part (inside) should be 128
    assert out.getpixel((5, 9)) == 128


def test_crop_beyond_width():
    """Cropping beyond image width should pad with zeros."""
    im = Image.new("L", (10, 10), 200)
    out = im.crop((5, 0, 15, 10))
    assert out.size == (10, 10)
    # Left part (inside) should be 200
    assert out.getpixel((0, 0)) == 200
    # Right part (outside) should be 0
    assert out.getpixel((9, 0)) == 0


def test_crop_beyond_height():
    """Cropping beyond image height should pad with zeros."""
    im = Image.new("L", (10, 10), 200)
    out = im.crop((0, 5, 10, 15))
    assert out.size == (10, 10)
    # Top part (inside) should be 200
    assert out.getpixel((5, 0)) == 200
    # Bottom part (outside) should be 0
    assert out.getpixel((5, 9)) == 0


def test_crop_fully_outside():
    """Completely outside crop should return all zeros."""
    im = Image.new("L", (10, 10), 200)
    out = im.crop((100, 100, 110, 110))
    assert out.size == (10, 10)
    assert out.getpixel((5, 5)) == 0


def test_crop_negative_both():
    """Crop starting before (0,0) and ending inside image."""
    im = Image.new("L", (10, 10), 128)
    out = im.crop((-3, -3, 5, 5))
    assert out.size == (8, 8)
    # Origin area (inside image after offset) should be 128
    assert out.getpixel((3, 3)) == 128
    # Corner area (outside image) should be 0
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# Crop produces correct size for out-of-bounds
# ---------------------------------------------------------------------------

def test_crop_oob_size():
    im = Image.new("L", (10, 10), 0)
    out = im.crop((-5, -5, 15, 15))
    assert out.size == (20, 20)


def test_crop_partial_oob_x1():
    im = Image.new("L", (10, 10), 0)
    out = im.crop((3, 3, 12, 7))
    assert out.size == (9, 4)


# ---------------------------------------------------------------------------
# Empty crop (zero area)
# ---------------------------------------------------------------------------

def test_crop_zero_width():
    im = Image.new("L", (10, 10), 128)
    out = im.crop((5, 5, 5, 8))  # zero width
    assert out.size == (0, 3)


def test_crop_zero_height():
    im = Image.new("L", (10, 10), 128)
    out = im.crop((3, 5, 8, 5))  # zero height
    assert out.size == (5, 0)


# ---------------------------------------------------------------------------
# RGB crop with out-of-bounds
# ---------------------------------------------------------------------------

def test_crop_oob_rgb_pads_black():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = im.crop((-2, -2, 5, 5))
    assert out.size == (7, 7)
    # Outside area padded with (0, 0, 0)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    # Inside area has the original color
    assert out.getpixel((2, 2)) == (100, 150, 200)


if __name__ == "__main__":
    pytest.main()
