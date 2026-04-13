"""
Tests adapted from upstream Pillow test_imageenhance.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageenhance.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageEnhance
from helper import hopper, assert_image_equal


def _half_transparent_image():
    """Returns an image, half transparent, half solid — from upstream."""
    im = hopper("RGB")
    transparent = Image.new("L", im.size, 0)
    solid = Image.new("L", (im.size[0] // 2, im.size[1]), 255)
    transparent.paste(solid, (0, 0))
    im.putalpha(transparent)
    return im


def test_alpha():
    """Alpha is preserved through image enhancement — from upstream.

    https://github.com/python-pillow/Pillow/issues/899
    """
    original = _half_transparent_image()

    for op in ("Color", "Brightness", "Contrast", "Sharpness"):
        for amount in (0, 0.5, 1.0):
            enhanced = getattr(ImageEnhance, op)(original).enhance(amount)
            assert enhanced.getbands() == original.getbands()
            assert_image_equal(
                enhanced.getchannel("A"),
                original.getchannel("A"),
            )


def test_alpha_la():
    """Alpha preserved through enhance on LA mode — derived from upstream."""
    original = hopper("L")
    alpha = Image.new("L", original.size, 128)
    original.putalpha(alpha)

    for op in ("Brightness", "Contrast", "Sharpness"):
        for amount in (0, 0.5, 1.0):
            enhanced = getattr(ImageEnhance, op)(original).enhance(amount)
            assert "A" in enhanced.getbands()
            assert_image_equal(
                enhanced.getchannel("A"),
                original.getchannel("A"),
            )


if __name__ == "__main__":
    pytest.main()
