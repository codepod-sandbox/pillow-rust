"""
Tests adapted from upstream Pillow test_image_putalpha.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_putalpha.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image


def test_interface():
    """putalpha with image and int — from upstream test_interface."""
    im = Image.new("RGBA", (1, 1), (1, 2, 3, 0))
    assert im.getpixel((0, 0)) == (1, 2, 3, 0)

    im = Image.new("RGBA", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3, 255)

    im.putalpha(Image.new("L", im.size, 4))
    assert im.getpixel((0, 0)) == (1, 2, 3, 4)

    im.putalpha(5)
    assert im.getpixel((0, 0)) == (1, 2, 3, 5)


def test_promote_rgb():
    """putalpha on RGB promotes to RGBA — from upstream test_promote."""
    im = Image.new("RGB", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)

    im.putalpha(4)
    assert im.mode == "RGBA"
    assert im.getpixel((0, 0)) == (1, 2, 3, 4)


def test_promote_l():
    """putalpha on L promotes to LA — from upstream test_promote."""
    im = Image.new("L", (1, 1), 1)
    assert im.getpixel((0, 0)) == 1

    im.putalpha(2)
    assert im.mode == "LA"
    assert im.getpixel((0, 0)) == (1, 2)


def test_putalpha_preserves_rgb():
    """putalpha should not change RGB values."""
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 255))
    im.putalpha(128)
    px = im.getpixel((0, 0))
    assert px[0] == 100
    assert px[1] == 150
    assert px[2] == 200
    assert px[3] == 128


def test_putalpha_image():
    """putalpha with an image mask — derived from upstream."""
    im = Image.new("RGBA", (3, 1), (10, 20, 30, 255))
    alpha = Image.new("L", (3, 1), 0)
    alpha.putpixel((0, 0), 100)
    alpha.putpixel((1, 0), 200)
    alpha.putpixel((2, 0), 50)
    im.putalpha(alpha)
    assert im.getpixel((0, 0))[3] == 100
    assert im.getpixel((1, 0))[3] == 200
    assert im.getpixel((2, 0))[3] == 50


if __name__ == "__main__":
    pytest.main()
