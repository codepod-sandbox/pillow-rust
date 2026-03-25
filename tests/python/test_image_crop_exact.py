"""Tests for Image.crop() — exact pixel values and boundary conditions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic crop
# ---------------------------------------------------------------------------

def test_crop_size():
    im = Image.new("L", (100, 100), 0)
    out = im.crop((10, 10, 60, 40))
    assert out.size == (50, 30)


def test_crop_preserves_mode():
    for mode, color in [("L", 128), ("RGB", (1, 2, 3)), ("RGBA", (1, 2, 3, 4))]:
        im = Image.new(mode, (50, 50), color)
        out = im.crop((5, 5, 25, 25))
        assert out.mode == mode


def test_crop_returns_new():
    im = Image.new("L", (50, 50), 0)
    out = im.crop((0, 0, 25, 25))
    assert out is not im


def test_crop_pixel_values():
    """Crop should extract the exact sub-rectangle."""
    im = Image.new("L", (10, 10), 0)
    # Paint a 3x3 block at (2,2)-(4,4) with value 200
    for y in range(2, 5):
        for x in range(2, 5):
            im.putpixel((x, y), 200)
    # Crop exactly that block
    out = im.crop((2, 2, 5, 5))
    assert out.size == (3, 3)
    assert out.getpixel((0, 0)) == 200
    assert out.getpixel((2, 2)) == 200


def test_crop_rgb_values():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((3, 4), (100, 150, 200))
    out = im.crop((3, 4, 5, 6))
    assert out.getpixel((0, 0)) == (100, 150, 200)


def test_crop_top_left():
    im = Image.new("L", (10, 10), 255)
    im.putpixel((0, 0), 100)
    out = im.crop((0, 0, 3, 3))
    assert out.getpixel((0, 0)) == 100


def test_crop_bottom_right():
    im = Image.new("L", (10, 10), 255)
    im.putpixel((9, 9), 50)
    out = im.crop((7, 7, 10, 10))
    assert out.getpixel((2, 2)) == 50


def test_crop_full_image():
    im = Image.new("L", (10, 10), 128)
    out = im.crop((0, 0, 10, 10))
    assert out.size == (10, 10)
    assert out.getpixel((5, 5)) == 128


def test_crop_width_1():
    im = Image.new("L", (10, 10), 0)
    for y in range(10):
        im.putpixel((5, y), 200)
    out = im.crop((5, 0, 6, 10))
    assert out.size == (1, 10)
    assert out.getpixel((0, 5)) == 200


def test_crop_height_1():
    im = Image.new("L", (10, 10), 0)
    for x in range(10):
        im.putpixel((x, 5), 200)
    out = im.crop((0, 5, 10, 6))
    assert out.size == (10, 1)
    assert out.getpixel((5, 0)) == 200


# ---------------------------------------------------------------------------
# Crop doesn't modify original
# ---------------------------------------------------------------------------

def test_crop_does_not_modify_original():
    im = Image.new("L", (10, 10), 100)
    out = im.crop((2, 2, 8, 8))
    out.putpixel((0, 0), 200)
    assert im.getpixel((2, 2)) == 100


# ---------------------------------------------------------------------------
# getbbox() — non-zero bounding box
# ---------------------------------------------------------------------------

def test_getbbox_uniform_image_returns_none():
    """All-zero (black) image: no non-zero pixels → None."""
    im = Image.new("L", (10, 10), 0)
    bbox = im.getbbox()
    assert bbox is None


def test_getbbox_single_pixel():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 200)
    bbox = im.getbbox()
    assert bbox == (5, 5, 6, 6)


def test_getbbox_full_image():
    """All-white image: bbox is entire image."""
    im = Image.new("L", (10, 10), 255)
    bbox = im.getbbox()
    assert bbox == (0, 0, 10, 10)


def test_getbbox_rectangle():
    im = Image.new("L", (20, 20), 0)
    for y in range(5, 10):
        for x in range(3, 15):
            im.putpixel((x, y), 200)
    bbox = im.getbbox()
    assert bbox == (3, 5, 15, 10)


def test_getbbox_rgb():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((3, 3), (255, 0, 0))
    bbox = im.getbbox()
    assert bbox == (3, 3, 4, 4)


if __name__ == "__main__":
    pytest.main()
