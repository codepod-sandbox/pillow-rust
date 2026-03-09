"""Adapted from upstream Pillow Tests/test_image_rotate.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image
from helper import hopper, assert_image, SUPPORTED_MODES


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_rotate_mode(mode):
    im = hopper(mode)
    out = im.rotate(45)
    assert out.mode == mode

def test_rotate_0():
    im = hopper("RGB")
    out = im.rotate(0)
    assert_image(out, "RGB", im.size)

def test_rotate_90_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(90)
    assert out.size == (50, 100)

def test_rotate_180_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(180)
    assert out.size == (100, 50)

def test_rotate_270_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(270)
    assert out.size == (50, 100)

def test_rotate_360():
    im = hopper("RGB")
    out = im.rotate(360)
    assert_image(out, "RGB", im.size)

def test_rotate_90_pixel():
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(90)
    assert out.size == (20, 10)
    assert out.getpixel((0, 9)) == (255, 0, 0)

def test_rotate_180_pixel():
    im = Image.new("RGB", (10, 10))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(180)
    assert out.getpixel((9, 9)) == (255, 0, 0)

def test_rotate_270_pixel():
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(270)
    assert out.size == (20, 10)
    assert out.getpixel((19, 0)) == (255, 0, 0)

def test_rotate_arbitrary():
    """Non-90 degree rotation should keep same dims and not crash."""
    im = Image.new("RGB", (100, 100), (0, 255, 0))
    out = im.rotate(45)
    assert_image(out, im.mode, im.size)


if __name__ == "__main__":
    pytest.main()
