"""
Tests adapted from upstream Pillow test_image_transpose.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_transpose.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image
from conftest import assert_image, assert_image_equal


def _make_hopper(mode="RGB"):
    """Create a non-square test image with unique pixels at corners."""
    im = Image.new(mode, (121, 127))
    if mode in ("RGB", "RGBA"):
        im.putpixel((1, 1), (255, 0, 0) if mode == "RGB" else (255, 0, 0, 255))
        im.putpixel((119, 1), (0, 255, 0) if mode == "RGB" else (0, 255, 0, 255))
        im.putpixel((1, 125), (0, 0, 255) if mode == "RGB" else (0, 0, 255, 255))
        im.putpixel((119, 125), (255, 255, 0) if mode == "RGB" else (255, 255, 0, 255))
    elif mode == "L":
        im.putpixel((1, 1), 100)
        im.putpixel((119, 1), 150)
        im.putpixel((1, 125), 200)
        im.putpixel((119, 125), 250)
    return im


# ---------------------------------------------------------------------------
# Transpose operations using Image.Transpose enum
# ---------------------------------------------------------------------------


def test_flip_left_right_L():
    im = _make_hopper("L")
    x, y = im.size
    out = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert out.mode == "L"
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, 1))


def test_flip_left_right_RGB():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert out.mode == "RGB"
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, 1))
    assert im.getpixel((x - 2, 1)) == out.getpixel((1, 1))


def test_flip_top_bottom_L():
    im = _make_hopper("L")
    x, y = im.size
    out = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    assert out.mode == "L"
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((1, y - 2))


def test_flip_top_bottom_RGB():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    assert out.mode == "RGB"
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((1, y - 2))
    assert im.getpixel((x - 2, 1)) == out.getpixel((x - 2, y - 2))


def test_rotate_90():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.ROTATE_90)
    assert out.mode == "RGB"
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, x - 2))
    assert im.getpixel((x - 2, 1)) == out.getpixel((1, 1))


def test_rotate_180():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.ROTATE_180)
    assert out.mode == "RGB"
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, y - 2))
    assert im.getpixel((x - 2, 1)) == out.getpixel((1, y - 2))


def test_rotate_270():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.ROTATE_270)
    assert out.mode == "RGB"
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, 1))
    assert im.getpixel((x - 2, 1)) == out.getpixel((y - 2, x - 2))


def test_transpose_op():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.TRANSPOSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, 1))
    assert im.getpixel((x - 2, 1)) == out.getpixel((1, x - 2))


def test_transverse_op():
    im = _make_hopper("RGB")
    x, y = im.size
    out = im.transpose(Image.Transpose.TRANSVERSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, x - 2))
    assert im.getpixel((x - 2, y - 2)) == out.getpixel((1, 1))


# ---------------------------------------------------------------------------
# Roundtrip tests
# ---------------------------------------------------------------------------


def test_roundtrip_flip_lr():
    im = _make_hopper("RGB")
    out = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert_image_equal(im, out)


def test_roundtrip_flip_tb():
    im = _make_hopper("RGB")
    out = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    assert_image_equal(im, out)


def test_roundtrip_rotate_90_270():
    im = _make_hopper("RGB")
    out = im.transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.ROTATE_270)
    assert_image_equal(im, out)


def test_roundtrip_rotate_180():
    im = _make_hopper("RGB")
    out = im.transpose(Image.Transpose.ROTATE_180).transpose(Image.Transpose.ROTATE_180)
    assert_image_equal(im, out)


def test_transpose_equals_rotate90_flip_tb():
    """TRANSPOSE = ROTATE_90 + FLIP_TOP_BOTTOM."""
    im = _make_hopper("RGB")
    expected = im.transpose(Image.Transpose.TRANSPOSE)
    actual = im.transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    assert_image_equal(expected, actual)


def test_transpose_equals_rotate270_flip_lr():
    """TRANSPOSE = ROTATE_270 + FLIP_LEFT_RIGHT."""
    im = _make_hopper("RGB")
    expected = im.transpose(Image.Transpose.TRANSPOSE)
    actual = im.transpose(Image.Transpose.ROTATE_270).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert_image_equal(expected, actual)


def test_transverse_equals_rotate90_flip_lr():
    """TRANSVERSE = ROTATE_90 + FLIP_LEFT_RIGHT."""
    im = _make_hopper("RGB")
    expected = im.transpose(Image.Transpose.TRANSVERSE)
    actual = im.transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assert_image_equal(expected, actual)


def test_transverse_equals_rotate180_transpose():
    """TRANSVERSE = ROTATE_180 + TRANSPOSE."""
    im = _make_hopper("RGB")
    expected = im.transpose(Image.Transpose.TRANSVERSE)
    actual = im.transpose(Image.Transpose.ROTATE_180).transpose(Image.Transpose.TRANSPOSE)
    assert_image_equal(expected, actual)


# ---------------------------------------------------------------------------
# Upstream tests — test_image_transpose.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op", [
    Image.Transpose.FLIP_LEFT_RIGHT,
    Image.Transpose.FLIP_TOP_BOTTOM,
    Image.Transpose.ROTATE_90,
    Image.Transpose.ROTATE_180,
    Image.Transpose.ROTATE_270,
    Image.Transpose.TRANSPOSE,
    Image.Transpose.TRANSVERSE,
])
def test_sanity_L(op):
    """Upstream test_sanity: all operations work on L mode images."""
    im = _make_hopper("L")
    out = im.transpose(op)
    assert out.mode == "L"


@pytest.mark.parametrize("op", [
    Image.Transpose.FLIP_LEFT_RIGHT,
    Image.Transpose.FLIP_TOP_BOTTOM,
    Image.Transpose.ROTATE_90,
    Image.Transpose.ROTATE_180,
    Image.Transpose.ROTATE_270,
    Image.Transpose.TRANSPOSE,
    Image.Transpose.TRANSVERSE,
])
def test_sanity_RGBA(op):
    """Upstream test_sanity: all operations work on RGBA mode images."""
    im = _make_hopper("RGBA")
    out = im.transpose(op)
    assert out.mode == "RGBA"


def test_invalid_transpose():
    """Upstream: passing an invalid transpose value should raise."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((ValueError, Exception)):
        im.transpose(99)
