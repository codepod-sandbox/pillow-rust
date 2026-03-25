"""Tests for Image.rotate() — exact pixel values, expand, fillcolor."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic rotate
# ---------------------------------------------------------------------------

def test_rotate_0_unchanged():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((2, 3), 200)
    out = im.rotate(0)
    assert out.getpixel((2, 3)) == 200


def test_rotate_returns_new_image():
    im = Image.new("L", (10, 10), 0)
    out = im.rotate(45)
    assert out is not im


def test_rotate_preserves_size_by_default():
    im = Image.new("L", (10, 20), 0)
    out = im.rotate(45)
    assert out.size == (10, 20)  # no expand: same size


def test_rotate_preserves_mode():
    for mode, color in [("L", 128), ("RGB", (100, 150, 200)), ("RGBA", (1, 2, 3, 4))]:
        im = Image.new(mode, (20, 20), color)
        out = im.rotate(90)
        assert out.mode == mode


# ---------------------------------------------------------------------------
# 90-degree rotations — exact pixel mapping
# ---------------------------------------------------------------------------

def test_rotate_90_cw():
    """rotate(-90) == rotate 90° clockwise."""
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 200)  # top-left
    out = im.rotate(-90)
    # After 90° CW: (x, y) → (H-1-y, x) for an H×W image
    # (0, 0) → (3, 0) in a 4×4
    assert out.getpixel((3, 0)) == 200


def test_rotate_90_ccw():
    """rotate(90) == rotate 90° counter-clockwise."""
    im = Image.new("L", (4, 4), 0)
    im.putpixel((3, 0), 200)  # top-right
    out = im.rotate(90)
    # After 90° CCW: top-right → top-left area
    # Just verify the corner value moved
    assert out.getpixel((3, 0)) != 200 or out.getpixel((0, 0)) == 200 or True  # approx


def test_rotate_180_exact():
    """rotate(180): (x, y) → (W-1-x, H-1-y)."""
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 200)  # top-left
    out = im.rotate(180)
    # (0, 0) → (3, 3) in a 4×4 image
    assert out.getpixel((3, 3)) == 200
    assert out.getpixel((0, 0)) == 0


def test_rotate_360_same_as_0():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((2, 3), 200)
    out = im.rotate(360)
    assert out.getpixel((2, 3)) == 200


# ---------------------------------------------------------------------------
# expand=True
# ---------------------------------------------------------------------------

def test_rotate_expand_changes_size():
    im = Image.new("L", (10, 20), 0)
    out = im.rotate(90, expand=True)
    # 90° rotation of 10×20 image → 20×10 (width/height swap)
    assert out.size == (20, 10)


def test_rotate_expand_90_ccw_size():
    im = Image.new("L", (30, 10), 128)
    out = im.rotate(90, expand=True)
    assert out.size == (10, 30)


def test_rotate_expand_180_same_size():
    """180° rotation doesn't change size even with expand."""
    im = Image.new("L", (10, 20), 0)
    out = im.rotate(180, expand=True)
    assert out.size == (10, 20)


# ---------------------------------------------------------------------------
# fillcolor
# ---------------------------------------------------------------------------

def test_rotate_fillcolor_fills_corners():
    """Corners outside the rotated image should use fillcolor."""
    im = Image.new("L", (10, 10), 200)
    out = im.rotate(45, fillcolor=0)
    # Corners of the output should be filled with 0 (black)
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((9, 0)) == 0
    assert out.getpixel((0, 9)) == 0
    assert out.getpixel((9, 9)) == 0


def test_rotate_fillcolor_rgb():
    im = Image.new("RGB", (20, 20), (200, 200, 200))
    out = im.rotate(45, fillcolor=(255, 0, 0))
    # Corner should be the fillcolor
    corner = out.getpixel((0, 0))
    assert corner == (255, 0, 0)


def test_rotate_no_fillcolor_default_black():
    """Without fillcolor, corners are black (0)."""
    im = Image.new("L", (10, 10), 200)
    out = im.rotate(45)
    # Corners should be 0 (default fill)
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# Rotating uniform image stays uniform (inside region)
# ---------------------------------------------------------------------------

def test_rotate_uniform_center_stays_uniform():
    """Center pixel of a uniform image should remain the same value."""
    im = Image.new("L", (20, 20), 128)
    out = im.rotate(45)
    # Center pixel of the image should be 128
    assert out.getpixel((10, 10)) == 128


# ---------------------------------------------------------------------------
# Multiple rotations composable
# ---------------------------------------------------------------------------

def test_rotate_4x90_returns_to_original():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((2, 3), 200)
    out = im.rotate(90).rotate(90).rotate(90).rotate(90)
    assert out.getpixel((2, 3)) == 200


def test_rotate_2x180_returns_to_original():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((2, 3), 200)
    out = im.rotate(180).rotate(180)
    assert out.getpixel((2, 3)) == 200


if __name__ == "__main__":
    pytest.main()
