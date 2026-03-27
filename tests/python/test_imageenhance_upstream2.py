"""
Tests adapted from upstream Pillow test_imageenhance.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageenhance.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageEnhance
from helper import hopper, assert_image_equal


def test_sanity():
    """All enhancers run without error on all modes — from upstream."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        ImageEnhance.Brightness(im).enhance(0.5)
        ImageEnhance.Contrast(im).enhance(0.5)
        ImageEnhance.Color(im).enhance(0.5) if mode == "RGB" else None
        ImageEnhance.Sharpness(im).enhance(0.5)


def test_crash():
    """Enhance small images — from upstream test_crash.

    Very small images used to cause a zero division error in equalize.
    """
    for mode in ("L", "RGB"):
        for size in ((1, 1), (2, 2), (3, 3)):
            im = Image.new(mode, size)
            for cls in (ImageEnhance.Brightness, ImageEnhance.Contrast,
                        ImageEnhance.Sharpness):
                cls(im).enhance(0.5)
            if mode == "RGB":
                ImageEnhance.Color(im).enhance(0.5)


def test_factor_one_identity():
    """Factor 1.0 returns original image — derived from upstream."""
    im = hopper("L")
    for cls in (ImageEnhance.Brightness, ImageEnhance.Contrast,
                ImageEnhance.Sharpness):
        out = cls(im).enhance(1.0)
        assert_image_equal(im, out)


def test_factor_one_identity_rgb():
    """Factor 1.0 on RGB returns original — derived from upstream."""
    im = hopper("RGB")
    for cls in (ImageEnhance.Brightness, ImageEnhance.Contrast,
                ImageEnhance.Color, ImageEnhance.Sharpness):
        out = cls(im).enhance(1.0)
        assert_image_equal(im, out)


def test_brightness_zero():
    """Brightness 0.0 gives black image — from upstream."""
    im = hopper("L")
    out = ImageEnhance.Brightness(im).enhance(0.0)
    black = Image.new("L", im.size, 0)
    assert_image_equal(out, black)


def test_brightness_two():
    """Brightness 2.0 doubles pixel values (clamped)."""
    im = Image.new("L", (1, 1), 100)
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((0, 0)) == 200


if __name__ == "__main__":
    pytest.main()
