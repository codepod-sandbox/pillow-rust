"""Tests for ImageOps color operations — colorize, grayscale, exact values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageOps


# ---------------------------------------------------------------------------
# colorize()
# ---------------------------------------------------------------------------

def test_colorize_black_to_black():
    """Black pixels map to the black color."""
    im = Image.new("L", (5, 5), 0)
    out = ImageOps.colorize(im, black=(255, 0, 0), white=(0, 0, 255))
    r, g, b = out.getpixel((0, 0))
    assert r == 255
    assert g == 0
    assert b == 0


def test_colorize_white_to_white():
    """White pixels map to the white color."""
    im = Image.new("L", (5, 5), 255)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(0, 255, 0))
    r, g, b = out.getpixel((0, 0))
    assert r == 0
    assert g == 255
    assert b == 0


def test_colorize_returns_RGB():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(255, 255, 255))
    assert out.mode == "RGB"


def test_colorize_preserves_size():
    im = Image.new("L", (20, 30), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(255, 255, 255))
    assert out.size == (20, 30)


def test_colorize_midpoint_blends():
    """Middle gray (128) should blend between black and white colors."""
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(200, 200, 200))
    r, g, b = out.getpixel((0, 0))
    # Should be approximately 100 (midpoint between 0 and 200)
    assert 80 <= r <= 120
    assert 80 <= g <= 120
    assert 80 <= b <= 120


def test_colorize_black_white_passthrough():
    """colorize(black=(0,0,0), white=(255,255,255)) should give grayscale RGB."""
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(255, 255, 255))
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 128) <= 5
    assert abs(g - 128) <= 5
    assert abs(b - 128) <= 5


# ---------------------------------------------------------------------------
# grayscale()
# ---------------------------------------------------------------------------

def test_grayscale_uniform_color():
    im = Image.new("RGB", (5, 5), (100, 100, 100))
    out = ImageOps.grayscale(im)
    assert abs(out.getpixel((0, 0)) - 100) <= 2


def test_grayscale_luminance_red():
    """Pure red → luminance ~76."""
    im = Image.new("RGB", (5, 5), (255, 0, 0))
    out = ImageOps.grayscale(im)
    # ITU-R 601: 0.299*255 ≈ 76
    assert abs(out.getpixel((0, 0)) - 76) <= 10


def test_grayscale_luminance_green():
    """Pure green → luminance ~150."""
    im = Image.new("RGB", (5, 5), (0, 255, 0))
    out = ImageOps.grayscale(im)
    # 0.587*255 ≈ 150
    assert abs(out.getpixel((0, 0)) - 150) <= 10


def test_grayscale_luminance_blue():
    """Pure blue → luminance ~29."""
    im = Image.new("RGB", (5, 5), (0, 0, 255))
    out = ImageOps.grayscale(im)
    # 0.114*255 ≈ 29
    assert abs(out.getpixel((0, 0)) - 29) <= 10


def test_grayscale_already_gray():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.grayscale(im)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


# ---------------------------------------------------------------------------
# equalize()
# ---------------------------------------------------------------------------

def test_equalize_flat_returns_flat():
    """Equalize a flat image — result should be flat."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.equalize(im)
    v = out.getpixel((0, 0))
    # All pixels should be the same in a flat image
    assert out.getpixel((5, 5)) == v


def test_equalize_RGB():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = ImageOps.equalize(im)
    assert out.mode == "RGB"
    assert out.size == (10, 10)


def test_equalize_expands_contrast():
    """After equalization, the image should span more of 0-255."""
    im = Image.new("L", (16, 16), 0)
    for v in range(128, 200):
        x, y = (v - 128) % 16, (v - 128) // 16
        im.putpixel((x, y), v)
    out = ImageOps.equalize(im)
    # Get all unique values
    all_vals = set(out.getpixel((x, y)) for y in range(16) for x in range(16))
    # Equalized image should span a wider range
    assert max(all_vals) - min(all_vals) > 50


# ---------------------------------------------------------------------------
# contain() and fit()
# ---------------------------------------------------------------------------

def test_contain_aspect_ratio_preserved():
    """contain() preserves aspect ratio."""
    im = Image.new("L", (200, 100), 128)
    out = ImageOps.contain(im, (50, 50))
    w, h = out.size
    # Should be 50x25 (2:1 ratio, fit in 50x50)
    assert w == 50 or h == 50
    # Aspect ratio preserved: w/h ≈ 2
    assert abs(w / h - 2.0) < 0.1


def test_contain_already_smaller():
    """contain() with larger target doesn't upscale."""
    im = Image.new("L", (20, 10), 128)
    out = ImageOps.contain(im, (100, 100))
    # Should stay at 20x10 (no upscaling)
    assert out.size == (20, 10)


def test_fit_always_fills_target():
    """fit() always returns exactly target size."""
    im = Image.new("L", (200, 100), 128)
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)


def test_fit_does_not_distort():
    """fit() should not distort (maintain aspect ratio by cropping)."""
    im = Image.new("RGB", (200, 100), (100, 150, 200))
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)
    assert out.mode == "RGB"


if __name__ == "__main__":
    pytest.main()
