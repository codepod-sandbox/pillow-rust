"""Tests for Image.resize() — resampling filter pixel accuracy."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Nearest neighbor — exact pixel mapping
# ---------------------------------------------------------------------------

def test_nearest_2x_upscale_exact():
    """2x upscale with NEAREST: each pixel becomes 2x2 block."""
    im = Image.new("L", (2, 2), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 200)
    im.putpixel((0, 1), 150)
    im.putpixel((1, 1), 50)
    out = im.resize((4, 4), Image.NEAREST)
    # Top-left 2x2 block should be 100
    assert out.getpixel((0, 0)) == 100
    assert out.getpixel((1, 0)) == 100
    assert out.getpixel((0, 1)) == 100
    assert out.getpixel((1, 1)) == 100
    # Top-right 2x2 block should be 200
    assert out.getpixel((2, 0)) == 200
    assert out.getpixel((3, 0)) == 200


def test_nearest_2x_downscale():
    """2x downscale with NEAREST."""
    im = Image.new("L", (4, 4), 0)
    # Fill with values
    for y in range(4):
        for x in range(4):
            im.putpixel((x, y), (x + y * 4) * 10)
    out = im.resize((2, 2), Image.NEAREST)
    # Just check the size
    assert out.size == (2, 2)


def test_nearest_uniform_image():
    """Uniform image resized with NEAREST stays uniform."""
    im = Image.new("L", (10, 10), 128)
    out = im.resize((5, 5), Image.NEAREST)
    for y in range(5):
        for x in range(5):
            assert out.getpixel((x, y)) == 128


def test_nearest_rgb():
    im = Image.new("RGB", (4, 4), (100, 150, 200))
    out = im.resize((8, 8), Image.NEAREST)
    assert out.getpixel((0, 0)) == (100, 150, 200)
    assert out.getpixel((7, 7)) == (100, 150, 200)


# ---------------------------------------------------------------------------
# Bilinear — smooth interpolation
# ---------------------------------------------------------------------------

def test_bilinear_uniform_exact():
    """Uniform image with BILINEAR stays same value."""
    im = Image.new("L", (10, 10), 200)
    out = im.resize((5, 5), Image.BILINEAR)
    for y in range(5):
        for x in range(5):
            assert abs(out.getpixel((x, y)) - 200) <= 2


def test_bilinear_gradient():
    """Bilinear on a gradient image should produce a smooth result."""
    im = Image.new("L", (10, 1), 0)
    for x in range(10):
        im.putpixel((x, 0), x * 25)  # 0, 25, 50, ..., 225
    out = im.resize((5, 1), Image.BILINEAR)
    # Result should be between 0 and 225
    for x in range(5):
        v = out.getpixel((x, 0))
        assert 0 <= v <= 225


# ---------------------------------------------------------------------------
# Bicubic — preserves smooth curves
# ---------------------------------------------------------------------------

def test_bicubic_uniform_exact():
    im = Image.new("L", (10, 10), 150)
    out = im.resize((5, 5), Image.BICUBIC)
    assert abs(out.getpixel((2, 2)) - 150) <= 5


def test_bicubic_returns_correct_size():
    im = Image.new("L", (100, 50), 100)
    out = im.resize((25, 25), Image.BICUBIC)
    assert out.size == (25, 25)


# ---------------------------------------------------------------------------
# Lanczos — high quality
# ---------------------------------------------------------------------------

def test_lanczos_uniform_exact():
    im = Image.new("L", (10, 10), 100)
    out = im.resize((5, 5), Image.LANCZOS)
    assert abs(out.getpixel((2, 2)) - 100) <= 5


def test_lanczos_preserves_mode():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = im.resize((5, 5), Image.LANCZOS)
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# Resample constants are available
# ---------------------------------------------------------------------------

def test_resample_constants_exist():
    assert hasattr(Image, "NEAREST")
    assert hasattr(Image, "BILINEAR")
    assert hasattr(Image, "BICUBIC")
    assert hasattr(Image, "LANCZOS")


def test_resample_constants_are_distinct():
    assert Image.NEAREST != Image.BILINEAR
    assert Image.BILINEAR != Image.BICUBIC
    assert Image.BICUBIC != Image.LANCZOS


# ---------------------------------------------------------------------------
# Resize to same size
# ---------------------------------------------------------------------------

def test_resize_to_same_size():
    im = Image.new("L", (10, 10), 128)
    out = im.resize((10, 10))
    assert out.size == (10, 10)
    assert out.getpixel((5, 5)) == 128


def test_resize_to_same_size_returns_new():
    im = Image.new("L", (10, 10), 128)
    out = im.resize((10, 10))
    assert out is not im


# ---------------------------------------------------------------------------
# Aspect ratio changes
# ---------------------------------------------------------------------------

def test_resize_change_aspect_ratio():
    im = Image.new("L", (10, 10), 128)
    out = im.resize((20, 5))
    assert out.size == (20, 5)


def test_resize_wide_to_tall():
    im = Image.new("L", (100, 10), 128)
    out = im.resize((10, 100))
    assert out.size == (10, 100)


if __name__ == "__main__":
    pytest.main()
