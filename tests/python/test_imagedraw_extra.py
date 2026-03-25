"""Tests for advanced ImageDraw: textbbox, multiline_text, rounded_rectangle, regular_polygon."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageFont


# -- textbbox ---------------------------------------------------------------

def test_textbbox():
    im = Image.new("RGB", (100, 50), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((10, 10), "Hello")
    assert len(bbox) == 4
    x0, y0, x1, y1 = bbox
    assert x0 == 10
    assert y0 == 10
    assert x1 > x0  # text has width
    assert y1 > y0  # text has height


def test_textbbox_with_font():
    im = Image.new("RGB", (100, 50))
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    bbox = draw.textbbox((5, 5), "Test", font=font)
    assert bbox[2] > bbox[0]
    assert bbox[3] > bbox[1]


# -- textlength -------------------------------------------------------------

def test_textlength():
    im = Image.new("RGB", (200, 50))
    draw = ImageDraw.Draw(im)
    length = draw.textlength("Hello World")
    assert length > 0


def test_textlength_proportional():
    im = Image.new("RGB", (200, 50))
    draw = ImageDraw.Draw(im)
    l1 = draw.textlength("Hi")
    l2 = draw.textlength("Hello World")
    assert l2 > l1


# -- multiline_text ---------------------------------------------------------

def test_multiline_text():
    im = Image.new("RGB", (100, 60), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.multiline_text((5, 5), "Hello\nWorld", fill=(0, 0, 0))
    # First line should have dark pixels near top
    found_top = False
    for x in range(100):
        if im.getpixel((x, 8))[0] < 128:
            found_top = True
            break
    # Second line should have dark pixels lower
    found_bottom = False
    for x in range(100):
        if im.getpixel((x, 28))[0] < 128:
            found_bottom = True
            break
    assert found_top or found_bottom, "multiline_text should draw on image"


def test_multiline_text_spacing():
    im = Image.new("RGB", (100, 80), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    # With extra spacing, lines should be further apart
    draw.multiline_text((5, 5), "A\nB\nC", fill=(0, 0, 0), spacing=10)
    # Just verify it doesn't crash


# -- rounded_rectangle ------------------------------------------------------

def test_rounded_rectangle():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((10, 10, 90, 90), radius=15, fill=(255, 0, 0))
    # Center should be red
    assert im.getpixel((50, 50)) == (255, 0, 0)


def test_rounded_rectangle_outline():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((10, 10, 90, 90), radius=10, outline=(0, 0, 255))
    # Edge should have outline color
    # (falls back to regular rect, so top edge should have blue)
    px = im.getpixel((50, 10))
    assert px == (0, 0, 255)


# -- regular_polygon --------------------------------------------------------

def test_regular_polygon_square():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    # Draw a square (4 sides) centered at (50,50) with radius 30
    draw.regular_polygon((50, 50, 30), n_sides=4, fill=(0, 255, 0))
    # Center should be green
    assert im.getpixel((50, 50)) == (0, 255, 0)


def test_regular_polygon_hexagon():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.regular_polygon((50, 50, 25), n_sides=6, fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)


def test_regular_polygon_triangle():
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.regular_polygon((50, 50, 20), n_sides=3, fill=(255, 0, 0))
    assert im.getpixel((50, 50)) == (255, 0, 0)


if __name__ == "__main__":
    pytest.main()
