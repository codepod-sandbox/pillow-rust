"""Tests for ImageDraw.line() — exact pixel values and width."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# Basic line drawing
# ---------------------------------------------------------------------------

def test_line_start_pixel():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (15, 5)], fill=200)
    assert im.getpixel((5, 5)) == 200


def test_line_end_pixel():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (15, 5)], fill=200)
    assert im.getpixel((15, 5)) == 200


def test_line_midpoint():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (15, 5)], fill=200)
    assert im.getpixel((10, 5)) == 200


def test_line_diagonal():
    """Diagonal line should draw some pixels."""
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(0, 0), (19, 19)], fill=200)
    # Start and end should be drawn
    assert im.getpixel((0, 0)) == 200
    assert im.getpixel((19, 19)) == 200
    # Some pixel in the middle
    found_mid = any(im.getpixel((x, x)) == 200 for x in range(5, 15))
    assert found_mid


def test_line_vertical_all_pixels():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(10, 0), (10, 19)], fill=200)
    for y in range(20):
        assert im.getpixel((10, y)) == 200


def test_line_horizontal_all_pixels():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(0, 10), (19, 10)], fill=200)
    for x in range(20):
        assert im.getpixel((x, 10)) == 200


# ---------------------------------------------------------------------------
# Line width
# ---------------------------------------------------------------------------

def test_line_width_1_single_pixel_thick():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (15, 10)], fill=200, width=1)
    assert im.getpixel((10, 10)) == 200
    assert im.getpixel((10, 11)) == 0  # only 1 pixel thick


def test_line_width_3():
    """Width-3 line should span 3 pixels vertically for horizontal line."""
    im = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=200, width=3)
    # Center row
    assert im.getpixel((15, 15)) == 200
    # One row above and below (for width 3)
    assert im.getpixel((15, 14)) == 200 or im.getpixel((15, 16)) == 200


def test_line_width_5():
    im = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=200, width=5)
    # Center should definitely be drawn
    assert im.getpixel((15, 15)) == 200


# ---------------------------------------------------------------------------
# Multi-point line (polyline)
# ---------------------------------------------------------------------------

def test_line_polyline():
    """Line with multiple points draws segments between each pair."""
    im = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (15, 15), (25, 5)], fill=200)
    # Start and end should be drawn
    assert im.getpixel((5, 5)) == 200
    assert im.getpixel((25, 5)) == 200
    # Mid-point should be drawn
    assert im.getpixel((15, 15)) == 200


# ---------------------------------------------------------------------------
# Line preserves other pixels
# ---------------------------------------------------------------------------

def test_line_does_not_affect_unrelated_pixels():
    im = Image.new("L", (30, 30), 100)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=200)
    # Far from line should be unchanged
    assert im.getpixel((15, 5)) == 100
    assert im.getpixel((15, 25)) == 100


# ---------------------------------------------------------------------------
# Line on RGB images
# ---------------------------------------------------------------------------

def test_line_rgb_red():
    im = Image.new("RGB", (30, 30), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=(255, 0, 0))
    assert im.getpixel((15, 15)) == (255, 0, 0)


def test_line_rgb_white():
    im = Image.new("RGB", (30, 30), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=(255, 255, 255))
    r, g, b = im.getpixel((15, 15))
    assert r == 255
    assert g == 255
    assert b == 255


# ---------------------------------------------------------------------------
# Line with fill=0
# ---------------------------------------------------------------------------

def test_line_fill_0_on_white():
    im = Image.new("L", (30, 30), 255)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 15), (25, 15)], fill=0)
    assert im.getpixel((15, 15)) == 0


if __name__ == "__main__":
    pytest.main()
