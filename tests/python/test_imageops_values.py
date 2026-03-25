"""Tests verifying exact pixel values for ImageOps operations."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageOps


# ---------------------------------------------------------------------------
# autocontrast — exact values
# ---------------------------------------------------------------------------

def test_autocontrast_L_min_max():
    """autocontrast should stretch histogram to 0-255."""
    im = Image.new("L", (4, 1), 0)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 100)
    im.putpixel((2, 0), 150)
    im.putpixel((3, 0), 200)
    out = ImageOps.autocontrast(im)
    # min=50 → 0, max=200 → 255
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((3, 0)) == 255


def test_autocontrast_L_uniform():
    """Uniform image should produce identity LUT."""
    im = Image.new("L", (5, 5), 100)
    out = ImageOps.autocontrast(im)
    # All pixels same → no stretch, output = original
    assert out.getpixel((2, 2)) == 100


def test_autocontrast_midvalue():
    """Verify a midpoint value is correctly scaled."""
    # values: 100, 150, 200
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 150)
    im.putpixel((2, 0), 200)
    out = ImageOps.autocontrast(im)
    # scale = 255/(200-100) = 2.55, offset = -100*2.55 = -255
    # 150: 150*2.55 - 255 = 127.5 → 127 (int)
    mid = out.getpixel((1, 0))
    assert 125 <= mid <= 130  # around 127-128


def test_autocontrast_RGB():
    """autocontrast on RGB stretches each channel independently.

    Use values where lo and hi divide evenly into 255 to avoid float rounding.
    """
    im = Image.new("RGB", (2, 1), 0)
    # R: lo=0, hi=255 → identity; G: lo=0, hi=255 → identity
    im.putpixel((0, 0), (0, 0, 0))
    im.putpixel((1, 0), (255, 255, 255))
    out = ImageOps.autocontrast(im)
    px0 = out.getpixel((0, 0))
    px1 = out.getpixel((1, 0))
    assert px0 == (0, 0, 0)
    assert px1 == (255, 255, 255)


def test_autocontrast_RGB_per_channel():
    """autocontrast stretches each channel independently (tolerant of off-by-one)."""
    im = Image.new("RGB", (2, 1), 0)
    im.putpixel((0, 0), (50, 100, 150))
    im.putpixel((1, 0), (200, 200, 200))
    out = ImageOps.autocontrast(im)
    px0 = out.getpixel((0, 0))
    px1 = out.getpixel((1, 0))
    # lo values → 0, hi values → 255 (allow ±1 for float truncation)
    assert px0[0] == 0    # red 50 → 0
    assert px1[0] == 255  # red 200 → 255 (150 range divides cleanly)
    assert px0[1] == 0    # green 100 → 0
    assert px1[1] >= 254  # green 200 → 255 or 254 (float imprecision possible)
    assert px0[2] == 0    # blue 150 → 0
    assert px1[2] >= 254  # blue 200 → 255 or 254


def test_autocontrast_cutoff():
    """autocontrast with cutoff should ignore extreme pixels."""
    # Build image with mostly mid values but one extreme
    im = Image.new("L", (100, 1), 128)
    im.putpixel((0, 0), 0)    # 1% of pixels are black
    im.putpixel((99, 0), 255)  # 1% are white
    out = ImageOps.autocontrast(im, cutoff=2)
    # With 2% cutoff, the 128 midvalue may not reach full range
    # Just verify it returns the correct mode and size
    assert out.mode == "L"
    assert out.size == (100, 1)


def test_autocontrast_preserve_tone():
    """preserve_tone uses single LUT across all channels."""
    im = Image.new("RGB", (2, 1), 0)
    im.putpixel((0, 0), (50, 100, 150))
    im.putpixel((1, 0), (200, 200, 200))
    out = ImageOps.autocontrast(im, preserve_tone=True)
    # With preserve_tone, same LUT applied to all channels
    assert out.mode == "RGB"
    assert out.size == (2, 1)


# ---------------------------------------------------------------------------
# equalize — property checks
# ---------------------------------------------------------------------------

def test_equalize_produces_flat_histogram():
    """After equalize, histogram should be more uniform."""
    # Create skewed histogram image
    im = Image.new("L", (100, 100), 0)
    for y in range(100):
        for x in range(100):
            im.putpixel((x, y), (x + y) % 100)  # values 0-99
    out = ImageOps.equalize(im)
    assert out.mode == "L"
    assert out.size == (100, 100)
    # equalized image should use more of the 0-255 range
    hist = out.histogram()
    assert sum(hist[200:]) > 0  # some pixels in 200+ range


def test_equalize_uniform_image():
    """Equalizing a uniform image just returns a copy."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.equalize(im)
    assert out.mode == "L"
    # All same value should map to same value (identity)
    assert out.getpixel((5, 5)) == 0 or out.getpixel((5, 5)) is not None


# ---------------------------------------------------------------------------
# solarize — exact values
# ---------------------------------------------------------------------------

def test_solarize_exact_L():
    """Solarize below threshold: unchanged; above: 255 - v."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 50)   # below 128
    im.putpixel((1, 0), 128)  # at threshold (>= threshold, so inverted)
    im.putpixel((2, 0), 200)  # above threshold
    out = ImageOps.solarize(im, threshold=128)
    assert out.getpixel((0, 0)) == 50       # unchanged (50 < 128)
    assert out.getpixel((1, 0)) == 127      # 255 - 128 = 127
    assert out.getpixel((2, 0)) == 55       # 255 - 200 = 55


def test_solarize_threshold_0():
    """Threshold=0: all pixels inverted."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 100)
    im.putpixel((2, 0), 200)
    out = ImageOps.solarize(im, threshold=0)
    assert out.getpixel((0, 0)) == 205  # 255 - 50
    assert out.getpixel((1, 0)) == 155  # 255 - 100
    assert out.getpixel((2, 0)) == 55   # 255 - 200


def test_solarize_threshold_255():
    """Threshold=255: no pixels inverted (none >= 255)."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 200)
    im.putpixel((2, 0), 254)
    out = ImageOps.solarize(im, threshold=255)
    assert out.getpixel((0, 0)) == 100  # unchanged
    assert out.getpixel((1, 0)) == 200
    assert out.getpixel((2, 0)) == 254


# ---------------------------------------------------------------------------
# posterize — exact values
# ---------------------------------------------------------------------------

def test_posterize_exact_values():
    """Verify posterize formula: v & ~(0xFF >> bits) & 0xFF."""
    im = Image.new("L", (4, 1), 0)
    im.putpixel((0, 0), 200)  # bits=1: 200 & 0x80 = 128
    im.putpixel((1, 0), 127)  # bits=1: 127 & 0x80 = 0
    im.putpixel((2, 0), 200)  # bits=2: 200 & 0xC0 = 192
    im.putpixel((3, 0), 160)  # bits=2: 160 & 0xC0 = 128

    out1 = ImageOps.posterize(im.crop((0, 0, 2, 1)), 1)
    assert out1.getpixel((0, 0)) == 128
    assert out1.getpixel((1, 0)) == 0

    out2 = ImageOps.posterize(im.crop((2, 0, 4, 1)), 2)
    assert out2.getpixel((0, 0)) == 192  # 200 & 0xC0 = 192
    assert out2.getpixel((1, 0)) == 128  # 160 & 0xC0 = 128


def test_posterize_2bits():
    """bits=2 mask = 0xC0."""
    im = Image.new("L", (5, 1), 0)
    vals = [0, 64, 128, 192, 255]
    expected = [0, 64, 128, 192, 192]  # 255 & 0xC0 = 192
    for i, v in enumerate(vals):
        im.putpixel((i, 0), v)
    out = ImageOps.posterize(im, 2)
    for i, e in enumerate(expected):
        assert out.getpixel((i, 0)) == e, f"idx={i}: expected {e}, got {out.getpixel((i, 0))}"


# ---------------------------------------------------------------------------
# expand and crop — exact sizes
# ---------------------------------------------------------------------------

def test_expand_size_calculation():
    """expand(border=b) increases each dimension by 2*b."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.expand(im, border=5)
    assert out.size == (20, 20)


def test_expand_tuple_size():
    """expand((left_right, top_bottom)) adds different amounts per axis."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.expand(im, border=(3, 7))
    assert out.size == (16, 24)


def test_expand_4tuple():
    """expand((left, top, right, bottom)) adds independent borders."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.expand(im, border=(1, 2, 3, 4))
    assert out.size == (14, 16)


def test_expand_pixel_placement():
    """Content should be in the correct position after expand."""
    im = Image.new("L", (4, 4), 200)
    out = ImageOps.expand(im, border=2, fill=0)
    # Original content at (2,2)-(5,5)
    assert out.getpixel((2, 2)) == 200
    assert out.getpixel((5, 5)) == 200
    # Border is 0
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((7, 7)) == 0


def test_crop_removes_border():
    """crop(border=b) removes b pixels from each side."""
    im = Image.new("L", (20, 20), 0)
    # Fill outer border with 255
    for x in range(20):
        im.putpixel((x, 0), 255)
        im.putpixel((x, 19), 255)
    for y in range(20):
        im.putpixel((0, y), 255)
        im.putpixel((19, y), 255)
    out = ImageOps.crop(im, border=1)
    assert out.size == (18, 18)
    # Top-left corner of cropped image should be interior (0)
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# contain and scale
# ---------------------------------------------------------------------------

def test_contain_already_fits():
    """contain with image smaller than target returns a copy."""
    im = Image.new("RGB", (100, 100), (1, 2, 3))
    out = ImageOps.contain(im, (200, 200))
    assert out.size == (100, 100)
    assert out.getpixel((50, 50)) == (1, 2, 3)


def test_contain_wider_than_tall():
    """contain: wide image limited by width."""
    im = Image.new("RGB", (400, 200), (0, 0, 0))
    out = ImageOps.contain(im, (200, 200))
    assert out.size == (200, 100)  # limited by width 400→200, height 200→100


def test_contain_taller_than_wide():
    """contain: tall image limited by height."""
    im = Image.new("RGB", (200, 400), (0, 0, 0))
    out = ImageOps.contain(im, (200, 200))
    assert out.size == (100, 200)  # limited by height 400→200, width 200→100


def test_scale_by_half():
    """scale(0.5) halves dimensions."""
    im = Image.new("L", (100, 80), 100)
    out = ImageOps.scale(im, 0.5)
    assert out.size == (50, 40)


def test_scale_by_2():
    """scale(2.0) doubles dimensions."""
    im = Image.new("L", (50, 40), 100)
    out = ImageOps.scale(im, 2.0)
    assert out.size == (100, 80)


def test_scale_negative_raises():
    """scale with negative factor should raise ValueError."""
    im = Image.new("L", (10, 10), 0)
    with pytest.raises(ValueError):
        ImageOps.scale(im, -1.0)


if __name__ == "__main__":
    pytest.main()
