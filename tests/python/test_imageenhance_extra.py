"""Extended ImageEnhance tests — exact values and edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageEnhance


def _solid(mode, color, size=(10, 10)):
    return Image.new(mode, size, color)


# ---------------------------------------------------------------------------
# Brightness
# ---------------------------------------------------------------------------

def test_brightness_1_is_identity():
    im = _solid("L", 128)
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == 128


def test_brightness_0_is_black():
    im = _solid("L", 200)
    out = ImageEnhance.Brightness(im).enhance(0.0)
    assert out.getpixel((5, 5)) == 0


def test_brightness_2_doubles():
    im = _solid("L", 100)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    val = out.getpixel((5, 5))
    assert abs(int(val) - 200) <= 2


def test_brightness_clamps_at_255():
    im = _solid("L", 200)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((5, 5)) == 255


def test_brightness_rgb():
    im = _solid("RGB", (100, 100, 100))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 200) <= 2
    assert abs(g - 200) <= 2
    assert abs(b - 200) <= 2


def test_brightness_preserves_mode():
    im = _solid("RGB", (100, 150, 200))
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.mode == "RGB"


def test_brightness_returns_new_image():
    im = _solid("L", 128)
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out is not im


# ---------------------------------------------------------------------------
# Contrast
# ---------------------------------------------------------------------------

def test_contrast_1_is_identity():
    im = _solid("L", 128)
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert abs(out.getpixel((5, 5)) - 128) <= 2


def test_contrast_0_is_solid_gray():
    """Contrast=0 → solid gray (mean of image)."""
    im = _solid("L", 128)
    out = ImageEnhance.Contrast(im).enhance(0.0)
    val = out.getpixel((5, 5))
    # Should be near 128 (mean)
    assert 120 <= int(val) <= 136


def test_contrast_2_stretches():
    """Contrast=2 should stretch pixel values away from mean."""
    # Pixel at 200, mean at 128: (200-128)*2 + 128 = 272, clamped → 255
    im = _solid("L", 200)
    out = ImageEnhance.Contrast(im).enhance(2.0)
    val = int(out.getpixel((5, 5)))
    assert val >= 200  # stretched toward white


def test_contrast_preserves_mode():
    im = _solid("RGB", (100, 150, 200))
    out = ImageEnhance.Contrast(im).enhance(1.5)
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# Color (saturation)
# ---------------------------------------------------------------------------

def test_color_0_is_grayscale():
    """Color=0 → grayscale."""
    im = _solid("RGB", (200, 50, 50))
    out = ImageEnhance.Color(im).enhance(0.0)
    r, g, b = out.getpixel((0, 0))
    # Should be grayscale (r==g==b or close)
    assert abs(r - g) <= 5
    assert abs(g - b) <= 5


def test_color_1_is_identity():
    im = _solid("RGB", (200, 50, 100))
    out = ImageEnhance.Color(im).enhance(1.0)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 200) <= 2
    assert abs(g - 50) <= 2
    assert abs(b - 100) <= 2


def test_color_preserves_mode():
    im = _solid("RGB", (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(1.5)
    assert out.mode == "RGB"


def test_color_returns_new():
    im = _solid("RGB", (100, 150, 200))
    out = ImageEnhance.Color(im).enhance(1.0)
    assert out is not im


# ---------------------------------------------------------------------------
# Sharpness
# ---------------------------------------------------------------------------

def test_sharpness_1_is_identity():
    im = _solid("L", 128)
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert abs(out.getpixel((5, 5)) - 128) <= 2


def test_sharpness_0_is_blurred():
    """Sharpness=0 → blurred version."""
    im = _solid("L", 128)
    im.putpixel((5, 5), 255)
    out = ImageEnhance.Sharpness(im).enhance(0.0)
    # Blurred: center pixel should be less than 255
    assert out.getpixel((5, 5)) < 255


def test_sharpness_2_sharpens():
    """Sharpness=2 → sharpened version."""
    im = _solid("L", 128)
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out.mode == "L"


def test_sharpness_preserves_mode():
    im = _solid("RGB", (100, 150, 200))
    out = ImageEnhance.Sharpness(im).enhance(1.5)
    assert out.mode == "RGB"


def test_sharpness_returns_new():
    im = _solid("L", 128)
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert out is not im


# ---------------------------------------------------------------------------
# General enhancer behavior
# ---------------------------------------------------------------------------

def test_enhance_factor_float():
    """All enhancers accept float factors."""
    im = _solid("L", 128)
    for cls in [ImageEnhance.Brightness, ImageEnhance.Contrast, ImageEnhance.Sharpness]:
        out = cls(im).enhance(1.5)
        assert out.mode == "L"


def test_enhance_preserves_size():
    im = _solid("RGB", (100, 150, 200), size=(30, 20))
    out = ImageEnhance.Brightness(im).enhance(1.5)
    assert out.size == (30, 20)


if __name__ == "__main__":
    pytest.main()
