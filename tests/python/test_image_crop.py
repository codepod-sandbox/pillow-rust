"""Adapted from upstream Pillow Tests/test_image_crop.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image
from helper import hopper, assert_image, assert_image_equal, SUPPORTED_MODES


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_crop(mode):
    im = hopper(mode)
    out = im.crop((50, 50, 100, 100))
    assert_image(out, mode, (50, 50))

def test_crop_no_args():
    """crop() with no args returns a full copy."""
    im = hopper("RGB")
    out = im.crop()
    assert_image_equal(im, out)

def test_crop_full():
    im = Image.new("RGB", (100, 100), (1, 2, 3))
    out = im.crop((0, 0, 100, 100))
    assert_image(out, "RGB", (100, 100))
    assert out.getpixel((0, 0)) == (1, 2, 3)

def test_crop_single_pixel():
    im = Image.new("RGB", (10, 10), (5, 6, 7))
    im.putpixel((3, 4), (99, 98, 97))
    out = im.crop((3, 4, 4, 5))
    assert_image(out, "RGB", (1, 1))
    assert out.getpixel((0, 0)) == (99, 98, 97)

def test_crop_preserves_pixels():
    im = Image.new("RGB", (100, 100), (42, 43, 44))
    out = im.crop((25, 25, 75, 75))
    assert out.getpixel((0, 0)) == (42, 43, 44)
    assert out.getpixel((24, 24)) == (42, 43, 44)

@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_crop_preserves_mode(mode):
    im = hopper(mode)
    out = im.crop((10, 10, 50, 50))
    assert out.mode == mode


if __name__ == "__main__":
    pytest.main()
