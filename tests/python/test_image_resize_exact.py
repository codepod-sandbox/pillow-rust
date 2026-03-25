"""Tests for Image.resize() — exact sizes, resampling, and edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Resize output sizes
# ---------------------------------------------------------------------------

def test_resize_exact_size():
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    out = im.resize((50, 50))
    assert out.size == (50, 50)


def test_resize_non_square():
    im = Image.new("L", (200, 100), 128)
    out = im.resize((80, 40))
    assert out.size == (80, 40)


def test_resize_upscale():
    im = Image.new("L", (10, 10), 128)
    out = im.resize((100, 100))
    assert out.size == (100, 100)


def test_resize_to_1x1():
    im = Image.new("L", (100, 100), 128)
    out = im.resize((1, 1))
    assert out.size == (1, 1)


def test_resize_from_1x1():
    im = Image.new("L", (1, 1), 128)
    out = im.resize((50, 50))
    assert out.size == (50, 50)


# ---------------------------------------------------------------------------
# Resize preserves mode
# ---------------------------------------------------------------------------

def test_resize_L_mode():
    im = Image.new("L", (100, 100), 128)
    out = im.resize((50, 50))
    assert out.mode == "L"


def test_resize_RGB_mode():
    im = Image.new("RGB", (100, 100), (100, 150, 200))
    out = im.resize((50, 50))
    assert out.mode == "RGB"


def test_resize_RGBA_mode():
    im = Image.new("RGBA", (100, 100), (100, 150, 200, 128))
    out = im.resize((50, 50))
    assert out.mode == "RGBA"


# ---------------------------------------------------------------------------
# Resize doesn't modify original
# ---------------------------------------------------------------------------

def test_resize_returns_new_image():
    im = Image.new("L", (100, 100), 128)
    out = im.resize((50, 50))
    assert out is not im


def test_resize_original_unchanged():
    im = Image.new("L", (100, 100), 128)
    out = im.resize((50, 50))
    assert im.size == (100, 100)


# ---------------------------------------------------------------------------
# Resize with resampling filters
# ---------------------------------------------------------------------------

def test_resize_nearest():
    im = Image.new("L", (10, 10), 100)
    out = im.resize((5, 5), Image.NEAREST)
    assert out.getpixel((2, 2)) == 100


def test_resize_bilinear():
    im = Image.new("L", (10, 10), 100)
    out = im.resize((5, 5), Image.BILINEAR)
    assert abs(out.getpixel((2, 2)) - 100) <= 5


def test_resize_bicubic():
    im = Image.new("L", (10, 10), 100)
    out = im.resize((5, 5), Image.BICUBIC)
    assert abs(out.getpixel((2, 2)) - 100) <= 5


def test_resize_lanczos():
    im = Image.new("L", (10, 10), 100)
    out = im.resize((5, 5), Image.LANCZOS)
    assert abs(out.getpixel((2, 2)) - 100) <= 5


# ---------------------------------------------------------------------------
# Resize uniform image stays uniform
# ---------------------------------------------------------------------------

def test_resize_uniform_stays_uniform():
    """Resizing a uniform image should give a uniform result."""
    for mode, color in [("L", 200), ("RGB", (50, 100, 150))]:
        im = Image.new(mode, (50, 50), color)
        out = im.resize((25, 25))
        if mode == "L":
            val = out.getpixel((12, 12))
            assert abs(int(val) - 200) <= 2
        else:
            r, g, b = out.getpixel((12, 12))
            assert abs(r - 50) <= 5
            assert abs(g - 100) <= 5
            assert abs(b - 150) <= 5


# ---------------------------------------------------------------------------
# thumbnail()
# ---------------------------------------------------------------------------

def test_thumbnail_respects_aspect_ratio():
    """thumbnail() preserves aspect ratio."""
    im = Image.new("RGB", (400, 200), (0, 0, 0))
    im.thumbnail((100, 100))
    w, h = im.size
    assert w == 100
    assert h == 50  # height scaled proportionally


def test_thumbnail_modifies_in_place():
    im = Image.new("RGB", (400, 200), (0, 0, 0))
    original_id = id(im)
    im.thumbnail((100, 100))
    assert id(im) == original_id  # same object


def test_thumbnail_already_fits():
    """thumbnail() doesn't upscale."""
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    im.thumbnail((100, 100))
    assert im.size == (50, 50)


if __name__ == "__main__":
    pytest.main()
