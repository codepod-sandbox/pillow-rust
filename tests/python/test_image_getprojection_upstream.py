"""
Tests adapted from upstream Pillow test_image_getprojection.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_getprojection.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_getprojection_L():
    """getprojection() on an L image returns two lists of correct length."""
    im = hopper("L")
    w, h = im.size
    hproj, vproj = im.getprojection()
    assert len(hproj) == w
    assert len(vproj) == h


def test_getprojection_RGB():
    """getprojection() on an RGB image returns two lists of correct length."""
    im = hopper("RGB")
    w, h = im.size
    hproj, vproj = im.getprojection()
    assert len(hproj) == w
    assert len(vproj) == h


def test_getprojection_blank():
    """getprojection() on a blank image has all zeros — from upstream."""
    im = Image.new("L", (10, 5), 0)
    hproj, vproj = im.getprojection()
    assert hproj == [0] * 10
    assert vproj == [0] * 5


def test_getprojection_single_pixel():
    """getprojection() with one lit pixel marks exactly one column and one row."""
    im = Image.new("L", (5, 5), 0)
    im.putpixel((2, 3), 255)
    hproj, vproj = im.getprojection()
    # Only column 2 and row 3 should be non-zero
    assert hproj[2] == 1
    assert vproj[3] == 1
    for x in range(5):
        if x != 2:
            assert hproj[x] == 0
    for y in range(5):
        if y != 3:
            assert vproj[y] == 0


def test_getprojection_full():
    """getprojection() on a fully-lit image: each value equals dimension."""
    im = Image.new("L", (4, 3), 255)
    hproj, vproj = im.getprojection()
    assert hproj == [3, 3, 3, 3]  # each column has h=3 non-zero pixels
    assert vproj == [4, 4, 4]     # each row has w=4 non-zero pixels


if __name__ == "__main__":
    pytest.main()
