"""
Tests adapted from upstream Pillow test_image_transpose.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_transpose.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from PIL.Image import Transpose
from helper import hopper, assert_image_equal

# Use L and RGB only (upstream also tests I;16 family which we don't support)
MODES = ["L", "RGB"]

HOPPER = {
    mode: hopper(mode).crop((0, 0, 121, 127)).copy()
    for mode in MODES
}


def test_flip_left_right():
    """FLIP_LEFT_RIGHT mirrors horizontally — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.FLIP_LEFT_RIGHT)
        assert out.mode == mode
        assert out.size == im.size

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((x - 2, 1))
        assert im.getpixel((x - 2, 1)) == out.getpixel((1, 1))
        assert im.getpixel((1, y - 2)) == out.getpixel((x - 2, y - 2))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((1, y - 2))


def test_flip_top_bottom():
    """FLIP_TOP_BOTTOM mirrors vertically — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.FLIP_TOP_BOTTOM)
        assert out.mode == mode
        assert out.size == im.size

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((1, y - 2))
        assert im.getpixel((x - 2, 1)) == out.getpixel((x - 2, y - 2))
        assert im.getpixel((1, y - 2)) == out.getpixel((1, 1))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((x - 2, 1))


def test_rotate_90():
    """ROTATE_90 swaps dimensions and rotates pixels — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.ROTATE_90)
        assert out.mode == mode
        assert out.size == im.size[::-1]

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((1, x - 2))
        assert im.getpixel((x - 2, 1)) == out.getpixel((1, 1))
        assert im.getpixel((1, y - 2)) == out.getpixel((y - 2, x - 2))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((y - 2, 1))


def test_rotate_180():
    """ROTATE_180 preserves dimensions and rotates pixels — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.ROTATE_180)
        assert out.mode == mode
        assert out.size == im.size

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((x - 2, y - 2))
        assert im.getpixel((x - 2, 1)) == out.getpixel((1, y - 2))
        assert im.getpixel((1, y - 2)) == out.getpixel((x - 2, 1))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((1, 1))


def test_rotate_270():
    """ROTATE_270 swaps dimensions and rotates pixels — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.ROTATE_270)
        assert out.mode == mode
        assert out.size == im.size[::-1]

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((y - 2, 1))
        assert im.getpixel((x - 2, 1)) == out.getpixel((y - 2, x - 2))
        assert im.getpixel((1, y - 2)) == out.getpixel((1, 1))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((1, x - 2))


def test_transpose_op():
    """TRANSPOSE swaps axes — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.TRANSPOSE)
        assert out.mode == mode
        assert out.size == im.size[::-1]

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((1, 1))
        assert im.getpixel((x - 2, 1)) == out.getpixel((1, x - 2))
        assert im.getpixel((1, y - 2)) == out.getpixel((y - 2, 1))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((y - 2, x - 2))


def test_transverse():
    """TRANSVERSE is anti-transpose — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]
        out = im.transpose(Transpose.TRANSVERSE)
        assert out.mode == mode
        assert out.size == im.size[::-1]

        x, y = im.size
        assert im.getpixel((1, 1)) == out.getpixel((y - 2, x - 2))
        assert im.getpixel((x - 2, 1)) == out.getpixel((y - 2, 1))
        assert im.getpixel((1, y - 2)) == out.getpixel((1, x - 2))
        assert im.getpixel((x - 2, y - 2)) == out.getpixel((1, 1))


def test_roundtrip():
    """Transpose roundtrip identities — from upstream."""
    for mode in MODES:
        im = HOPPER[mode]

        def transpose(first, second):
            return im.transpose(first).transpose(second)

        assert_image_equal(
            im, transpose(Transpose.FLIP_LEFT_RIGHT, Transpose.FLIP_LEFT_RIGHT)
        )
        assert_image_equal(
            im, transpose(Transpose.FLIP_TOP_BOTTOM, Transpose.FLIP_TOP_BOTTOM)
        )
        assert_image_equal(im, transpose(Transpose.ROTATE_90, Transpose.ROTATE_270))
        assert_image_equal(im, transpose(Transpose.ROTATE_180, Transpose.ROTATE_180))
        assert_image_equal(
            im.transpose(Transpose.TRANSPOSE),
            transpose(Transpose.ROTATE_90, Transpose.FLIP_TOP_BOTTOM),
        )
        assert_image_equal(
            im.transpose(Transpose.TRANSPOSE),
            transpose(Transpose.ROTATE_270, Transpose.FLIP_LEFT_RIGHT),
        )
        assert_image_equal(
            im.transpose(Transpose.TRANSVERSE),
            transpose(Transpose.ROTATE_90, Transpose.FLIP_LEFT_RIGHT),
        )
        assert_image_equal(
            im.transpose(Transpose.TRANSVERSE),
            transpose(Transpose.ROTATE_270, Transpose.FLIP_TOP_BOTTOM),
        )
        assert_image_equal(
            im.transpose(Transpose.TRANSVERSE),
            transpose(Transpose.ROTATE_180, Transpose.TRANSPOSE),
        )


if __name__ == "__main__":
    pytest.main()
