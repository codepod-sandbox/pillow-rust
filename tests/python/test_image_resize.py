"""Adapted from upstream Pillow Tests/test_image_resize.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image
from helper import hopper, assert_image, SUPPORTED_MODES


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_resize_mode_preserved(mode):
    im = hopper(mode)
    out = im.resize((64, 64))
    assert_image(out, mode, (64, 64))

def test_resize_reduce():
    out = hopper("RGB").resize((15, 12))
    assert_image(out, "RGB", (15, 12))

def test_resize_enlarge():
    out = hopper("RGB").resize((212, 195))
    assert_image(out, "RGB", (212, 195))

def test_resize_1x1():
    out = hopper("RGB").resize((1, 1))
    assert_image(out, "RGB", (1, 1))

@pytest.mark.parametrize("resample", [
    Image.NEAREST, Image.BILINEAR, Image.BICUBIC, Image.LANCZOS
])
def test_resize_filters(resample):
    out = hopper("RGB").resize((15, 12), resample=resample)
    assert_image(out, "RGB", (15, 12))

@pytest.mark.parametrize("resample", [
    Image.NEAREST, Image.BILINEAR, Image.BICUBIC, Image.LANCZOS
])
def test_enlarge_filters(resample):
    out = hopper("RGB").resize((212, 195), resample=resample)
    assert_image(out, "RGB", (212, 195))


if __name__ == "__main__":
    pytest.main()
