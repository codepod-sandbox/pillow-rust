"""Tests for additional ImageOps functions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageOps


# ---------------------------------------------------------------------------
# equalize
# ---------------------------------------------------------------------------

def test_equalize_L():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 1), 200)
    out = ImageOps.equalize(im)
    assert out.mode == "L"
    assert out.size == (10, 10)

def test_equalize_RGB():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    out = ImageOps.equalize(im)
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# solarize
# ---------------------------------------------------------------------------

def test_solarize_below_threshold():
    im = Image.new("L", (10, 10), 50)
    out = ImageOps.solarize(im, threshold=128)
    assert out.getpixel((5, 5)) == 50  # below threshold, unchanged

def test_solarize_above_threshold():
    im = Image.new("L", (10, 10), 200)
    out = ImageOps.solarize(im, threshold=128)
    assert out.getpixel((5, 5)) == 55  # 255 - 200

def test_solarize_RGB():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageOps.solarize(im, threshold=128)
    r, g, b = out.getpixel((5, 5))
    assert r == 55   # 255 - 200
    assert g == 100  # below threshold
    assert b == 50   # below threshold


# ---------------------------------------------------------------------------
# posterize
# ---------------------------------------------------------------------------

def test_posterize_1bit():
    im = Image.new("L", (10, 10), 200)
    out = ImageOps.posterize(im, 1)
    assert out.getpixel((5, 5)) == 128  # 200 & 0x80

def test_posterize_4bit():
    im = Image.new("L", (10, 10), 200)
    out = ImageOps.posterize(im, 4)
    assert out.getpixel((5, 5)) == 192  # 200 & 0xF0

def test_posterize_8bit():
    im = Image.new("L", (10, 10), 200)
    out = ImageOps.posterize(im, 8)
    assert out.getpixel((5, 5)) == 200  # unchanged

def test_posterize_RGB():
    im = Image.new("RGB", (10, 10), (200, 150, 100))
    out = ImageOps.posterize(im, 4)
    r, g, b = out.getpixel((5, 5))
    assert r == 192  # 200 & 0xF0
    assert g == 144  # 150 & 0xF0
    assert b == 96   # 100 & 0xF0


# ---------------------------------------------------------------------------
# expand
# ---------------------------------------------------------------------------

def test_expand_uniform():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageOps.expand(im, border=5, fill=(0, 0, 0))
    assert out.size == (20, 20)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((7, 7)) == (255, 0, 0)

def test_expand_tuple():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageOps.expand(im, border=(2, 3), fill=0)
    assert out.size == (14, 16)

def test_expand_4tuple():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageOps.expand(im, border=(1, 2, 3, 4), fill=0)
    assert out.size == (14, 16)
    assert out.getpixel((1, 2)) == (255, 0, 0)


# ---------------------------------------------------------------------------
# crop (ImageOps.crop, not Image.crop)
# ---------------------------------------------------------------------------

def test_crop_uniform():
    im = Image.new("RGB", (20, 20), (255, 0, 0))
    out = ImageOps.crop(im, border=5)
    assert out.size == (10, 10)

def test_crop_tuple():
    im = Image.new("RGB", (20, 20), (255, 0, 0))
    out = ImageOps.crop(im, border=(2, 3))
    assert out.size == (16, 14)


# ---------------------------------------------------------------------------
# colorize
# ---------------------------------------------------------------------------

def test_colorize_basic():
    im = Image.new("L", (10, 10), 0)
    out = ImageOps.colorize(im, black=(255, 0, 0), white=(0, 0, 255))
    assert out.mode == "RGB"
    assert out.getpixel((5, 5)) == (255, 0, 0)  # black pixel → black color

def test_colorize_white():
    im = Image.new("L", (10, 10), 255)
    out = ImageOps.colorize(im, black=(255, 0, 0), white=(0, 0, 255))
    assert out.getpixel((5, 5)) == (0, 0, 255)  # white pixel → white color

def test_colorize_mid():
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(255, 255, 255))
    r, g, b = out.getpixel((5, 5))
    assert 120 < r < 136  # roughly 128

def test_colorize_string_colors():
    im = Image.new("L", (10, 10), 0)
    out = ImageOps.colorize(im, black="red", white="blue")
    assert out.mode == "RGB"
    assert out.getpixel((5, 5)) == (255, 0, 0)


# ---------------------------------------------------------------------------
# exif_transpose
# ---------------------------------------------------------------------------

def test_exif_transpose_noop():
    im = Image.new("RGB", (10, 10), (100, 200, 50))
    out = ImageOps.exif_transpose(im)
    assert out.size == (10, 10)
    assert out.getpixel((5, 5)) == (100, 200, 50)


if __name__ == "__main__":
    pytest.main()
