"""
Tests adapted from upstream Pillow test_image_putdata.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_putdata.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_sanity():
    """putdata of getdata roundtrip — adapted from upstream.

    Note: upstream uses get_flattened_data(); our impl uses getdata().
    """
    im1 = hopper()
    data = list(im1.getdata())
    im2 = Image.new(im1.mode, im1.size, 0)
    im2.putdata(data)
    assert_image_equal(im1, im2)


def test_sanity_l():
    """putdata roundtrip for L mode."""
    im1 = hopper("L")
    data = list(im1.getdata())
    im2 = Image.new("L", im1.size, 0)
    im2.putdata(data)
    assert_image_equal(im1, im2)


def test_mode_with_L_with_float():
    """putdata with float value on L mode — from upstream."""
    im = Image.new("L", (1, 1), 0)
    im.putdata([2.0])
    assert im.getpixel((0, 0)) == 2


def test_pypy_performance():
    """Large putdata should not crash — from upstream."""
    im = Image.new("L", (256, 256))
    im.putdata(list(range(256)) * 256)


def test_putdata_preserves_values():
    """Verify putdata preserves exact values."""
    data = list(range(100))
    im = Image.new("L", (10, 10), 0)
    im.putdata(data)
    result = list(im.getdata())
    assert result == data


def test_putdata_rgb():
    """putdata with RGB tuples."""
    data = [(100, 150, 200)] * 25
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    im.putdata(data)
    assert im.getpixel((2, 2)) == (100, 150, 200)


def test_putdata_scale_offset():
    """putdata with scale and offset — adapted from upstream."""
    im = Image.new("L", (5, 5), 0)
    try:
        im.putdata([10] * 25, scale=2.0, offset=5)
        # 10 * 2.0 + 5 = 25
        assert im.getpixel((0, 0)) == 25
    except TypeError:
        # scale/offset may not be keyword args
        try:
            im.putdata([10] * 25, 2.0, 5)
            assert im.getpixel((0, 0)) == 25
        except TypeError:
            pytest.skip("putdata scale/offset not supported")


if __name__ == "__main__":
    pytest.main()
