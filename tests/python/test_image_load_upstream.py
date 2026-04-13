"""
Tests adapted from upstream Pillow test_image_load.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_load.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_sanity():
    """im.load() returns a PixelAccess object that supports read/write — from upstream."""
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        px = im.load()
        assert px is not None
        # Can read a pixel
        _ = px[0, 0]
        # Can write a pixel (just no exception raised)
        if mode == "L":
            px[0, 0] = 128
        elif mode == "RGB":
            px[0, 0] = (128, 0, 0)
        else:  # RGBA
            px[0, 0] = (128, 0, 0, 255)


def test_load_returns_same_object_twice():
    """Calling im.load() twice returns a usable PixelAccess each time — derived from upstream."""
    im = hopper("RGB")
    px1 = im.load()
    px2 = im.load()
    # Both should let us read the same pixel
    assert px1[5, 5] == px2[5, 5]


def test_pixel_access_read_write_roundtrip():
    """Writing via PixelAccess and reading back gives the same value — derived from upstream."""
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    px = im.load()
    px[3, 7] = (200, 100, 50)
    assert px[3, 7] == (200, 100, 50)


def test_pixel_access_L_roundtrip():
    """PixelAccess roundtrip for L mode image — derived from upstream."""
    im = Image.new("L", (10, 10), 0)
    px = im.load()
    px[2, 4] = 200
    assert px[2, 4] == 200


def test_pixel_access_RGBA_roundtrip():
    """PixelAccess roundtrip for RGBA mode image — derived from upstream."""
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    px = im.load()
    px[1, 1] = (10, 20, 30, 128)
    assert px[1, 1] == (10, 20, 30, 128)


if __name__ == "__main__":
    pytest.main()
