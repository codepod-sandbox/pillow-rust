"""
Tests adapted from upstream Pillow test_image_mode.py, restricted to
supported modes (L, LA, RGB, RGBA).

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_mode.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image


def test_getmodebands_L():
    """getmodebands('L') == 1 — from upstream."""
    assert Image.getmodebands("L") == 1


def test_getmodebands_LA():
    """getmodebands('LA') == 2 — from upstream."""
    assert Image.getmodebands("LA") == 2


def test_getmodebands_RGB():
    """getmodebands('RGB') == 3 — from upstream."""
    assert Image.getmodebands("RGB") == 3


def test_getmodebands_RGBA():
    """getmodebands('RGBA') == 4 — from upstream."""
    assert Image.getmodebands("RGBA") == 4


def test_mode_property_L():
    """Image.new('L').mode == 'L' — from upstream."""
    im = Image.new("L", (1, 1))
    assert im.mode == "L"


def test_mode_property_LA():
    """Image.new('LA').mode == 'LA' — from upstream."""
    im = Image.new("LA", (1, 1))
    assert im.mode == "LA"


def test_mode_property_RGB():
    """Image.new('RGB').mode == 'RGB' — from upstream."""
    im = Image.new("RGB", (1, 1))
    assert im.mode == "RGB"


def test_mode_property_RGBA():
    """Image.new('RGBA').mode == 'RGBA' — from upstream."""
    im = Image.new("RGBA", (1, 1))
    assert im.mode == "RGBA"


def test_new_L_size():
    """Image.new('L') has correct size — from upstream."""
    im = Image.new("L", (100, 100))
    assert im.size == (100, 100)
    assert im.width == 100
    assert im.height == 100


def test_new_RGB_size():
    """Image.new('RGB') has correct size — from upstream."""
    im = Image.new("RGB", (50, 75))
    assert im.size == (50, 75)


if __name__ == "__main__":
    pytest.main()
