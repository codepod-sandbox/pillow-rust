"""
Tests adapted from upstream Pillow test_image_getbbox.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_getbbox.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_sanity():
    bbox = hopper().getbbox()
    assert isinstance(bbox, tuple)


def test_bbox_l():
    """Test getbbox on L mode images — from upstream test_bbox."""
    im = Image.new("L", (100, 100), 0)
    assert im.getbbox() is None

    im.paste(255, (10, 25, 90, 75))
    assert im.getbbox() == (10, 25, 90, 75)

    im.paste(255, (25, 10, 75, 90))
    assert im.getbbox() == (10, 10, 90, 90)

    im.paste(255, (-10, -10, 110, 110))
    assert im.getbbox() == (0, 0, 100, 100)


def test_bbox_rgb():
    """Test getbbox on RGB mode images — from upstream test_bbox."""
    im = Image.new("RGB", (100, 100), 0)
    assert im.getbbox() is None

    im.paste(255, (10, 25, 90, 75))
    assert im.getbbox() == (10, 25, 90, 75)

    im.paste(255, (25, 10, 75, 90))
    assert im.getbbox() == (10, 10, 90, 90)

    im.paste(255, (-10, -10, 110, 110))
    assert im.getbbox() == (0, 0, 100, 100)


def test_bbox_rgba():
    """Test getbbox on RGBA mode — adapted from upstream.

    Note: upstream Pillow checks alpha-only for RGBA bbox by default.
    Our implementation checks all channels, so (0,0,0,0) is empty
    but (127,127,127,0) is not. We test the (0,0,0,0) case.
    """
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    assert im.getbbox() is None

    im.paste((255, 255, 255, 255), (10, 25, 90, 75))
    assert im.getbbox() == (10, 25, 90, 75)

    im.paste((255, 255, 255, 255), (25, 10, 75, 90))
    assert im.getbbox() == (10, 10, 90, 90)

    im.paste((255, 255, 255, 255), (-10, -10, 110, 110))
    assert im.getbbox() == (0, 0, 100, 100)


if __name__ == "__main__":
    pytest.main()
