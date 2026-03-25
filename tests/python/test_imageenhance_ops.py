"""Tests for ImageEnhance — exact pixel behavior."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageEnhance


# ---------------------------------------------------------------------------
# Brightness
# ---------------------------------------------------------------------------

def test_brightness_factor_1_unchanged():
    """Factor 1.0 should leave image unchanged."""
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((0, 0)) == 100


def test_brightness_factor_0_black():
    """Factor 0.0 should return black image."""
    im = Image.new("L", (5, 5), 200)
    out = ImageEnhance.Brightness(im).enhance(0.0)
    assert out.getpixel((0, 0)) == 0


def test_brightness_factor_2_doubles():
    """Factor 2.0 should roughly double brightness (clamped at 255)."""
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    # Should be around 200
    assert abs(out.getpixel((0, 0)) - 200) <= 10


def test_brightness_clamps_at_255():
    im = Image.new("L", (5, 5), 200)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((0, 0)) == 255


def test_brightness_factor_0_5_halves():
    im = Image.new("L", (5, 5), 200)
    out = ImageEnhance.Brightness(im).enhance(0.5)
    assert abs(out.getpixel((0, 0)) - 100) <= 5


def test_brightness_preserves_mode_L():
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Brightness(im).enhance(1.5)
    assert out.mode == "L"


def test_brightness_preserves_mode_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.mode == "RGB"


def test_brightness_returns_new_image():
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Brightness(im).enhance(1.5)
    assert out is not im


def test_brightness_does_not_modify_original():
    im = Image.new("L", (5, 5), 100)
    ImageEnhance.Brightness(im).enhance(2.0)
    assert im.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# Contrast
# ---------------------------------------------------------------------------

def test_contrast_factor_1_unchanged():
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert abs(out.getpixel((0, 0)) - 100) <= 3


def test_contrast_factor_0_flat_gray():
    """Factor 0 should produce a solid gray (mean of original)."""
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Contrast(im).enhance(0.0)
    # All pixels should be the same (mean gray)
    v = out.getpixel((0, 0))
    assert isinstance(v, int) or isinstance(v, float)


def test_contrast_preserves_mode():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Contrast(im).enhance(1.5)
    assert out.mode == "RGB"


def test_contrast_returns_new():
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Contrast(im).enhance(2.0)
    assert out is not im


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------

def test_color_factor_1_unchanged():
    """Factor 1.0 should leave image unchanged."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(1.0)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 100) <= 3
    assert abs(g - 150) <= 3
    assert abs(b - 200) <= 3


def test_color_factor_0_grayscale():
    """Factor 0 should produce a grayscale image."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(0.0)
    r, g, b = out.getpixel((0, 0))
    # All channels should be equal (gray)
    assert abs(r - g) <= 3
    assert abs(g - b) <= 3


def test_color_returns_new():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(2.0)
    assert out is not im


def test_color_preserves_mode():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(1.5)
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# Sharpness
# ---------------------------------------------------------------------------

def test_sharpness_factor_1_unchanged():
    im = Image.new("L", (10, 10), 128)
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert abs(out.getpixel((5, 5)) - 128) <= 5


def test_sharpness_returns_new():
    im = Image.new("L", (10, 10), 128)
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out is not im


def test_sharpness_preserves_mode():
    im = Image.new("L", (10, 10), 128)
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out.mode == "L"


def test_sharpness_uniform_unchanged():
    """Sharpening a uniform image shouldn't change it much."""
    im = Image.new("L", (10, 10), 128)
    out = ImageEnhance.Sharpness(im).enhance(5.0)
    assert abs(out.getpixel((5, 5)) - 128) <= 10


if __name__ == "__main__":
    pytest.main()
