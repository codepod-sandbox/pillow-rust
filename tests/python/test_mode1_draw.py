"""Tests for mode '1' conversion, ImageDraw.point, chord, multiline_textbbox."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw


# -- convert to mode '1' (binary) ------------------------------------------

def test_convert_rgb_to_1():
    im = Image.new("RGB", (10, 10), (200, 200, 200))
    im.putpixel((5, 5), (50, 50, 50))
    b = im.convert("1")
    assert b.getpixel((0, 0)) == 255  # bright
    assert b.getpixel((5, 5)) == 0    # dark


def test_convert_l_to_1():
    im = Image.new("L", (10, 10), 200)
    im.putpixel((0, 0), 50)
    b = im.convert("1")
    assert b.getpixel((0, 0)) == 0
    assert b.getpixel((5, 5)) == 255


def test_convert_1_threshold_boundary():
    im = Image.new("L", (4, 1), 0)
    im.putpixel((0, 0), 127)
    im.putpixel((1, 0), 128)
    im.putpixel((2, 0), 0)
    im.putpixel((3, 0), 255)
    b = im.convert("1")
    assert b.getpixel((0, 0)) == 0    # 127 < 128
    assert b.getpixel((1, 0)) == 255  # 128 >= 128
    assert b.getpixel((2, 0)) == 0
    assert b.getpixel((3, 0)) == 255


def test_convert_1_mode_is_l():
    """Mode '1' is stored as L internally."""
    im = Image.new("L", (5, 5), 200)
    b = im.convert("1")
    assert b.mode == "L"


# -- ImageDraw.point --------------------------------------------------------

def test_draw_point_tuples():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.point([(3, 3), (7, 7)], fill=(255, 0, 0))
    assert im.getpixel((3, 3)) == (255, 0, 0)
    assert im.getpixel((7, 7)) == (255, 0, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_draw_point_flat():
    im = Image.new("L", (10, 10), 0)
    draw = ImageDraw.Draw(im)
    draw.point([1, 1, 5, 5], fill=200)
    assert im.getpixel((1, 1)) == 200
    assert im.getpixel((5, 5)) == 200


def test_draw_point_single():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.point([(5, 5)], fill=(0, 255, 0))
    assert im.getpixel((5, 5)) == (0, 255, 0)


# -- ImageDraw.chord --------------------------------------------------------

def test_draw_chord():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.chord((10, 10, 90, 90), 0, 180, fill=(0, 255, 0))
    assert im.getpixel((50, 50)) == (0, 255, 0)


# -- multiline_textbbox -----------------------------------------------------

def test_multiline_textbbox():
    im = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(im)
    bbox = draw.multiline_textbbox((10, 10), "Hello\nWorld")
    assert len(bbox) == 4
    assert bbox[2] > bbox[0]  # has width
    assert bbox[3] > bbox[1]  # has height


def test_multiline_textbbox_single_line():
    im = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(im)
    bbox = draw.multiline_textbbox((0, 0), "Hello")
    # Single line: 5 chars * 8px = 40 wide, 16 tall
    assert bbox == (0, 0, 40, 16)


if __name__ == "__main__":
    pytest.main()
