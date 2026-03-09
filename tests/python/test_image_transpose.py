"""Adapted from upstream Pillow Tests/test_image_transpose.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image
from helper import hopper, assert_image, assert_image_equal


def _make_marker():
    """Non-square image with a unique pixel at (1,1)."""
    im = Image.new("RGB", (121, 127))
    im.putpixel((1, 1), (255, 0, 0))
    return im


def test_flip_left_right():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.FLIP_LEFT_RIGHT)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, 1))

def test_flip_top_bottom():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.FLIP_TOP_BOTTOM)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((1, y - 2))

def test_rotate_90():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_90)
    assert out.mode == im.mode
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, x - 2))

def test_rotate_180():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_180)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, y - 2))

def test_rotate_270():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_270)
    assert out.mode == im.mode
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, 1))

def test_transpose():
    """TRANSPOSE = mirror along main diagonal."""
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.TRANSPOSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, 1))

def test_transverse():
    """TRANSVERSE = mirror along anti-diagonal."""
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.TRANSVERSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, x - 2))

def test_roundtrip_flip_lr():
    im = _make_marker()
    out = im.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_LEFT_RIGHT)
    assert_image_equal(im, out)

def test_roundtrip_flip_tb():
    im = _make_marker()
    out = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_TOP_BOTTOM)
    assert_image_equal(im, out)

def test_roundtrip_rotate():
    im = _make_marker()
    out = im.transpose(Image.ROTATE_90).transpose(Image.ROTATE_270)
    assert_image_equal(im, out)

def test_roundtrip_rotate_180():
    im = _make_marker()
    out = im.transpose(Image.ROTATE_180).transpose(Image.ROTATE_180)
    assert_image_equal(im, out)

def test_transpose_L():
    im = Image.new("L", (121, 127))
    im.putpixel((1, 1), 200)
    out = im.transpose(Image.FLIP_LEFT_RIGHT)
    assert out.mode == "L"
    assert out.getpixel((119, 1)) == 200


if __name__ == "__main__":
    pytest.main()
