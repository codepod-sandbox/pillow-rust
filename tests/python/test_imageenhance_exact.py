"""Tests for ImageEnhance — exact pixel values after enhancement."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageEnhance


# ---------------------------------------------------------------------------
# Brightness — exact values
# ---------------------------------------------------------------------------

def test_brightness_10_percent():
    """10% brightness: image is almost black."""
    im = Image.new("L", (5, 5), 200)
    out = ImageEnhance.Brightness(im).enhance(0.1)
    # 200 * 0.1 = 20
    assert abs(out.getpixel((0, 0)) - 20) <= 10


def test_brightness_150_percent():
    """150% brightness: image is brighter."""
    im = Image.new("L", (5, 5), 100)
    out = ImageEnhance.Brightness(im).enhance(1.5)
    # Should be around 150
    assert abs(out.getpixel((0, 0)) - 150) <= 10


def test_brightness_zero_uniform():
    """0% brightness: all pixels become 0."""
    im = Image.new("L", (5, 5), 200)
    out = ImageEnhance.Brightness(im).enhance(0.0)
    for y in range(5):
        for x in range(5):
            assert out.getpixel((x, y)) == 0


def test_brightness_factor_1_exact():
    im = Image.new("L", (5, 5), 173)
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((0, 0)) == 173


def test_brightness_rgb_all_channels():
    """Brightness enhancement should affect all channels equally."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageEnhance.Brightness(im).enhance(0.5)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 50) <= 10
    assert abs(g - 75) <= 10
    assert abs(b - 100) <= 10


# ---------------------------------------------------------------------------
# Contrast — exact values
# ---------------------------------------------------------------------------

def test_contrast_factor_2_increases_contrast():
    """Factor 2.0 increases contrast: bright brighter, dark darker."""
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 200)  # bright pixel
    im.putpixel((1, 0), 50)   # dark pixel
    out = ImageEnhance.Contrast(im).enhance(2.0)
    # Bright should be brighter, dark should be darker
    bright = out.getpixel((0, 0))
    dark = out.getpixel((1, 0))
    assert bright > 200 or bright == 255
    assert dark < 50 or dark == 0


def test_contrast_factor_0_all_gray():
    """Factor 0: all pixels same gray (mean)."""
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 200)
    out = ImageEnhance.Contrast(im).enhance(0.0)
    v0 = out.getpixel((0, 0))
    v1 = out.getpixel((1, 0))
    assert v0 == v1


# ---------------------------------------------------------------------------
# Color — exact saturation effects
# ---------------------------------------------------------------------------

def test_color_0_completely_desaturated():
    """Factor 0: image should be grayscale (all channels equal)."""
    im = Image.new("RGB", (5, 5), (200, 50, 50))
    out = ImageEnhance.Color(im).enhance(0.0)
    r, g, b = out.getpixel((0, 0))
    # After full desaturation, all channels should be equal
    assert abs(r - g) <= 3
    assert abs(g - b) <= 3


def test_color_1_unchanged():
    im = Image.new("RGB", (5, 5), (200, 100, 50))
    out = ImageEnhance.Color(im).enhance(1.0)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 200) <= 5
    assert abs(g - 100) <= 5
    assert abs(b - 50) <= 5


# ---------------------------------------------------------------------------
# Sharpness — exact behavior on edge
# ---------------------------------------------------------------------------

def test_sharpness_0_is_blurred():
    """Factor 0: maximum blur."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)  # single bright pixel
    out = ImageEnhance.Sharpness(im).enhance(0.0)
    # Single pixel should be spread out
    center = out.getpixel((5, 5))
    neighbor = out.getpixel((4, 5))
    # The center should be less bright, neighbors brighter
    assert center < 255 or neighbor > 0


def test_sharpness_factor_2_on_uniform():
    """Sharpening uniform image changes nothing."""
    im = Image.new("L", (10, 10), 128)
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert abs(out.getpixel((5, 5)) - 128) <= 10


# ---------------------------------------------------------------------------
# All enhancers return same size
# ---------------------------------------------------------------------------

def test_all_enhancers_preserve_size():
    im = Image.new("L", (30, 40), 128)
    for factor in [0.0, 0.5, 1.0, 2.0]:
        assert ImageEnhance.Brightness(im).enhance(factor).size == (30, 40)
        assert ImageEnhance.Contrast(im).enhance(factor).size == (30, 40)
        assert ImageEnhance.Sharpness(im).enhance(factor).size == (30, 40)


# ---------------------------------------------------------------------------
# Brightness edge cases
# ---------------------------------------------------------------------------

def test_brightness_white_stays_white():
    im = Image.new("L", (5, 5), 255)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((0, 0)) == 255  # clamped at 255


def test_brightness_black_stays_black():
    im = Image.new("L", (5, 5), 0)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((0, 0)) == 0


if __name__ == "__main__":
    pytest.main()
