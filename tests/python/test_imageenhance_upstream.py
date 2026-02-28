"""Tests for PIL.ImageEnhance module."""

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
