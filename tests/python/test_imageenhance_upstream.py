"""
Tests for PIL.ImageEnhance module.

Tests adapted from upstream Pillow test_imageenhance.py:
  https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageenhance.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

from PIL import Image, ImageEnhance


# --- Brightness ---

def test_brightness_factor_0():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Brightness(im).enhance(0.0)
    assert out.getpixel((5, 5)) == (0, 0, 0)


def test_brightness_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_brightness_factor_2():
    im = Image.new("RGB", (10, 10), (100, 50, 25))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    px = out.getpixel((5, 5))
    assert px == (200, 100, 50)


def test_brightness_clamp():
    im = Image.new("RGB", (10, 10), (200, 200, 200))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    px = out.getpixel((5, 5))
    assert px == (255, 255, 255)


def test_brightness_L():
    im = Image.new("L", (10, 10), 100)
    out = ImageEnhance.Brightness(im).enhance(0.5)
    assert out.getpixel((5, 5)) == 50


# --- Contrast ---

def test_contrast_factor_0():
    """Factor 0 should produce a uniform gray image."""
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Contrast(im).enhance(0.0)
    px = out.getpixel((5, 5))
    # All channels should be the same gray value
    assert px[0] == px[1] == px[2]


def test_contrast_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_contrast_L():
    im = Image.new("L", (10, 10), 100)
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert out.getpixel((5, 5)) == 100


# --- Color (saturation) ---

def test_color_factor_0():
    """Factor 0 should produce grayscale."""
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageEnhance.Color(im).enhance(0.0)
    px = out.getpixel((5, 5))
    assert px[0] == px[1] == px[2]  # grayscale


def test_color_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Color(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


# --- Sharpness ---

def test_sharpness_factor_0():
    """Factor 0 should be blurred."""
    im = Image.new("RGB", (20, 20), (0, 0, 0))
    im.putpixel((10, 10), (255, 255, 255))
    out = ImageEnhance.Sharpness(im).enhance(0.0)
    assert out.size == (20, 20)
    assert out.mode == "RGB"


def test_sharpness_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_sharpness_factor_2():
    im = Image.new("RGB", (20, 20), (100, 100, 100))
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out.size == (20, 20)


# --- General ---

def test_enhance_preserves_size():
    im = Image.new("RGB", (50, 30), (100, 150, 200))
    for Enhancer in [ImageEnhance.Brightness, ImageEnhance.Contrast,
                     ImageEnhance.Color, ImageEnhance.Sharpness]:
        out = Enhancer(im).enhance(1.5)
        assert out.size == (50, 30)
        assert out.mode == "RGB"


# --- Upstream tests ---

def test_sanity():
    """Upstream test_sanity: all enhancers run without error.

    Adapted from test_imageenhance.py in Pillow.
    """
    im = Image.new("RGB", (128, 128))
    for Enhancer in [ImageEnhance.Color, ImageEnhance.Contrast,
                     ImageEnhance.Brightness, ImageEnhance.Sharpness]:
        for factor in (0.0, 0.5, 1.0, 2.0):
            out = Enhancer(im).enhance(factor)
            assert out.mode == "RGB"
            assert out.size == (128, 128)


def test_crash():
    """Upstream test_crash: Sharpness on a 1x1 image must not crash.

    Adapted from test_imageenhance.py in Pillow (issue with tiny images
    in the smooth filter path).
    """
    im = Image.new("RGB", (1, 1))
    ImageEnhance.Sharpness(im).enhance(0)


def test_alpha_preserved_brightness():
    """Upstream: alpha channel unchanged after Brightness enhancement.

    Adapted from test_imageenhance.py in Pillow.
    """
    im = Image.new("RGBA", (10, 10), (100, 100, 100, 200))
    out = ImageEnhance.Brightness(im).enhance(0.5)
    # Alpha must be unchanged
    assert out.getpixel((5, 5))[3] == 200


def test_alpha_preserved_contrast():
    """Upstream: alpha channel unchanged after Contrast enhancement."""
    im = Image.new("RGBA", (10, 10), (100, 100, 100, 128))
    out = ImageEnhance.Contrast(im).enhance(2.0)
    assert out.getpixel((5, 5))[3] == 128


def test_alpha_preserved_color():
    """Upstream: alpha channel unchanged after Color enhancement."""
    im = Image.new("RGBA", (10, 10), (200, 100, 50, 64))
    out = ImageEnhance.Color(im).enhance(0.0)
    assert out.getpixel((5, 5))[3] == 64


def test_alpha_preserved_sharpness():
    """Upstream: alpha channel unchanged after Sharpness enhancement."""
    im = Image.new("RGBA", (10, 10), (100, 100, 100, 200))
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out.getpixel((5, 5))[3] == 200
