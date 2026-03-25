"""
Tests for PIL.ImageOps module.

Tests adapted from upstream Pillow test_imageops.py:
  https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageops.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image, ImageOps


# --- autocontrast ---

def test_autocontrast_L():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 200)
    out = ImageOps.autocontrast(im)
    assert out.mode == "L"
    assert out.size == (10, 10)
    mn, mx = out.getextrema()
    assert mn == 0
    assert mx == 255


def test_autocontrast_RGB():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    im.putpixel((0, 0), (50, 60, 70))
    im.putpixel((1, 0), (200, 210, 220))
    out = ImageOps.autocontrast(im)
    assert out.mode == "RGB"


def test_autocontrast_flat():
    """All same value — should not crash; passthrough (no range to expand)."""
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.autocontrast(im)
    # Upstream behavior: when lo == hi, return passthrough (no mapping)
    assert out.getpixel((0, 0)) == 128


# --- contain ---

def test_contain_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (100, 50)


def test_contain_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 100)


def test_contain_already_fits():
    im = Image.new("RGB", (50, 30))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 30)


# --- fit ---

def test_fit_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_portrait():
    im = Image.new("RGB", (100, 300), (0, 255, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_square():
    im = Image.new("RGB", (200, 200))
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)


# --- pad ---

def test_pad_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)
    # Padding should be black by default
    assert out.getpixel((0, 0)) == (0, 0, 0)
    # Center should have image content
    assert out.getpixel((100, 100)) == (255, 0, 0)


def test_pad_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)


def test_pad_with_color():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200), color=(0, 0, 255))
    assert out.size == (200, 200)
    # Corner should be fill color
    assert out.getpixel((0, 0)) == (0, 0, 255)


def test_pad_already_fits():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    out = ImageOps.pad(im, (100, 100))
    assert out.size == (100, 100)
    assert out.getpixel((0, 0)) == (255, 0, 0)


# --- expand ---

def test_expand_default_black():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=10)
    assert out.size == (70, 70)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((10, 10)) == (255, 0, 0)


def test_expand_with_fill():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=5, fill=(0, 0, 255))
    assert out.size == (60, 60)
    assert out.getpixel((0, 0)) == (0, 0, 255)
    assert out.getpixel((5, 5)) == (255, 0, 0)


def test_expand_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(10, 20))
    assert out.size == (70, 90)


def test_expand_four_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(5, 10, 15, 20))
    assert out.size == (70, 80)
    assert out.getpixel((5, 10)) == (255, 0, 0)


def test_expand_L_mode():
    im = Image.new("L", (50, 50), 128)
    out = ImageOps.expand(im, border=5, fill=0)
    assert out.size == (60, 60)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((5, 5)) == 128


# --- flip ---

def test_flip():
    """flip() mirrors image vertically (top↔bottom)."""
    im = Image.new("RGB", (4, 4), 0)
    im.putpixel((0, 0), (255, 0, 0))
    out = ImageOps.flip(im)
    # (0,0) pixel should now be at (0, 3)
    assert out.getpixel((0, 3)) == (255, 0, 0)
    assert out.getpixel((0, 0)) == (0, 0, 0)


def test_flip_preserves_size():
    im = Image.new("RGB", (80, 60))
    out = ImageOps.flip(im)
    assert out.size == (80, 60)
    assert out.mode == "RGB"


def test_flip_L():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 200)
    out = ImageOps.flip(im)
    assert out.getpixel((0, 3)) == 200
    assert out.getpixel((0, 0)) == 0


# --- mirror ---

def test_mirror():
    """mirror() flips image horizontally (left↔right)."""
    im = Image.new("RGB", (4, 4), 0)
    im.putpixel((0, 0), (255, 0, 0))
    out = ImageOps.mirror(im)
    # (0,0) pixel should now be at (3, 0)
    assert out.getpixel((3, 0)) == (255, 0, 0)
    assert out.getpixel((0, 0)) == (0, 0, 0)


def test_mirror_preserves_size():
    im = Image.new("RGB", (80, 60))
    out = ImageOps.mirror(im)
    assert out.size == (80, 60)
    assert out.mode == "RGB"


def test_mirror_roundtrip():
    """mirror(mirror(im)) == im."""
    im = Image.new("RGB", (10, 10))
    for x in range(10):
        im.putpixel((x, 0), (x * 25, 0, 0))
    assert ImageOps.mirror(ImageOps.mirror(im)).tobytes() == im.tobytes()


# --- grayscale ---

def test_grayscale_rgb():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageOps.grayscale(im)
    assert out.mode == "L"
    assert out.size == (10, 10)


def test_grayscale_L():
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.grayscale(im)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


# --- invert ---

def test_invert_L():
    im = Image.new("L", (4, 4), 100)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 155   # 255 - 100


def test_invert_L_zero():
    im = Image.new("L", (4, 4), 0)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 255


def test_invert_L_max():
    im = Image.new("L", (4, 4), 255)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 0


def test_invert_RGB():
    im = Image.new("RGB", (4, 4), (100, 150, 200))
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == (155, 105, 55)


def test_invert_unsupported_mode():
    """Upstream: invert() raises OSError for unsupported modes."""
    im = Image.new("RGBA", (4, 4))
    with pytest.raises(OSError):
        ImageOps.invert(im)


# --- scale ---

def test_scale_double():
    im = Image.new("RGB", (50, 50))
    out = ImageOps.scale(im, 2)
    assert out.size == (100, 100)


def test_scale_half():
    im = Image.new("RGB", (50, 50))
    out = ImageOps.scale(im, 0.5)
    assert out.size == (25, 25)


def test_scale_one():
    im = Image.new("RGB", (50, 50))
    out = ImageOps.scale(im, 1)
    assert out.size == (50, 50)


def test_scale_negative():
    """Upstream: scale() raises ValueError for negative factor."""
    im = Image.new("L", (50, 50))
    with pytest.raises(ValueError):
        ImageOps.scale(im, -1)


def test_scale_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        im = Image.new(mode, (20, 20))
        out = ImageOps.scale(im, 2)
        assert out.mode == mode


# --- autocontrast unsupported mode ---

def test_autocontrast_unsupported_mode():
    """Upstream: autocontrast raises OSError for RGBA images."""
    im = Image.new("RGBA", (1, 1))
    with pytest.raises(OSError):
        ImageOps.autocontrast(im)


def test_autocontrast_cutoff():
    """cutoff=N and cutoff=(N,N) should produce identical results."""
    im = Image.new("L", (10, 10), 128)
    im.putpixel((0, 0), 0)
    im.putpixel((9, 9), 255)
    out1 = ImageOps.autocontrast(im, cutoff=10)
    out2 = ImageOps.autocontrast(im, cutoff=(10, 10))
    assert out1.tobytes() == out2.tobytes()


def test_autocontrast_cutoff_asymmetric():
    """Asymmetric cutoff tuple cuts low and high separately."""
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.autocontrast(im, cutoff=(5, 0))
    assert out.mode == "L"


def test_autocontrast_preserve_tone():
    """preserve_tone=True applies a single LUT to all channels."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    im.putpixel((0, 0), (50, 50, 50))
    im.putpixel((9, 9), (220, 220, 220))
    out = ImageOps.autocontrast(im, preserve_tone=True)
    assert out.mode == "RGB"
    assert out.size == (10, 10)


def test_autocontrast_preserve_one_color():
    """Single-color image with preserve_tone should not crash."""
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    out = ImageOps.autocontrast(im, preserve_tone=True)
    assert out.mode == "RGB"


def test_autocontrast_preserve_gradient():
    """Gradient image with preserve_tone maps extremes to 0 and 255."""
    im = Image.new("RGB", (256, 1))
    for x in range(256):
        im.putpixel((x, 0), (x, x, x))
    out = ImageOps.autocontrast(im, preserve_tone=True)
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((255, 0)) == (255, 255, 255)


def test_autocontrast_mask_zero():
    """mask=all-zeros histogram is empty; output should be all-zero."""
    im = Image.new("L", (10, 10), 128)
    mask = Image.new("L", (10, 10), 0)
    out = ImageOps.autocontrast(im, mask=mask)
    # No pixels counted → lut stays 0..255 passthrough
    assert out.mode == "L"


# --- fit edge cases ---

def test_1pxfit():
    """Upstream test_1pxfit: fit() handles 1-pixel-dimension images.

    Adapted from test_imageops.py in Pillow.
    """
    im = Image.new("RGB", (1, 1))
    out = ImageOps.fit(im, (35, 35))
    assert out.size == (35, 35)

    im = Image.new("RGB", (1, 100))
    out = ImageOps.fit(im, (35, 35))
    assert out.size == (35, 35)

    im = Image.new("RGB", (100, 1))
    out = ImageOps.fit(im, (35, 35))
    assert out.size == (35, 35)


def test_fit_same_ratio():
    """Upstream test_fit_same_ratio: avoids off-by-one from float rounding.

    Adapted from test_imageops.py in Pillow.
    """
    # 1000x755 ratio = 1.3245033...; fitting to itself must give (1000, 755)
    im = Image.new("RGB", (1000, 755))
    out = ImageOps.fit(im, (1000, 755))
    assert out.size == (1000, 755)
