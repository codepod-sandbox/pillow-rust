"""Adapted from upstream Pillow Tests/test_image_filter.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageFilter
from helper import hopper, assert_image


@pytest.mark.parametrize("mode", ["L", "RGB"])
def test_sanity_blur(mode):
    im = hopper(mode)
    out = im.filter(ImageFilter.BLUR)
    assert_image(out, mode, im.size)

@pytest.mark.parametrize("mode", ["L", "RGB"])
def test_sanity_sharpen(mode):
    im = hopper(mode)
    out = im.filter(ImageFilter.SHARPEN)
    assert_image(out, mode, im.size)

@pytest.mark.parametrize("mode", ["L", "RGB"])
def test_sanity_smooth(mode):
    im = hopper(mode)
    out = im.filter(ImageFilter.SMOOTH)
    assert_image(out, mode, im.size)

def test_gaussian_blur_default():
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur())
    assert_image(out, "RGB", im.size)

def test_gaussian_blur_radius():
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur(5))
    assert_image(out, "RGB", im.size)

@pytest.mark.parametrize("mode", ["L", "RGB"])
def test_filter_preserves_mode(mode):
    for filt in (ImageFilter.BLUR, ImageFilter.SHARPEN, ImageFilter.SMOOTH):
        im = hopper(mode)
        out = im.filter(filt)
        assert out.mode == mode, f"{filt.name} changed mode"

def test_crash_small_images():
    """Filter on tiny images should not crash."""
    for size in [(1, 1), (2, 2), (3, 3)]:
        im = Image.new("RGB", size, (100, 100, 100))
        out = im.filter(ImageFilter.SMOOTH)
        assert_image(out, "RGB", size)


if __name__ == "__main__":
    pytest.main()
