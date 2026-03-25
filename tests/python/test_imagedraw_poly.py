"""Tests for ImageDraw polygon operations — exact fill behavior."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# polygon() fill
# ---------------------------------------------------------------------------

def test_polygon_square_fills_interior():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (15, 15), (5, 15)], fill=200)
    # Interior
    assert im.getpixel((10, 10)) == 200


def test_polygon_square_outside_unchanged():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (15, 15), (5, 15)], fill=200)
    # Outside
    assert im.getpixel((0, 0)) == 0
    assert im.getpixel((19, 19)) == 0


def test_polygon_triangle_fills_interior():
    im = Image.new("L", (30, 30), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(15, 3), (3, 27), (27, 27)], fill=200)
    # Centroid at (15, 19)
    assert im.getpixel((15, 19)) == 200


def test_polygon_outline_only():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (15, 15), (5, 15)], outline=200)
    # Top edge
    assert im.getpixel((10, 5)) == 200


def test_polygon_fill_and_outline():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (15, 15), (5, 15)], fill=100, outline=255)
    # Interior has fill
    assert im.getpixel((10, 10)) == 100
    # Outline has different value
    assert im.getpixel((5, 5)) == 255


def test_polygon_preserves_mode():
    im = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (10, 15)], fill=200)
    assert im.mode == "L"


def test_polygon_rgb():
    im = Image.new("RGB", (30, 30), (0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (25, 5), (25, 25), (5, 25)], fill=(100, 150, 200))
    assert im.getpixel((15, 15)) == (100, 150, 200)


def test_polygon_fill_0_is_black():
    im = Image.new("L", (20, 20), 255)
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (15, 5), (15, 15), (5, 15)], fill=0)
    assert im.getpixel((10, 10)) == 0


# ---------------------------------------------------------------------------
# polygon() with many sides
# ---------------------------------------------------------------------------

def test_polygon_pentagon():
    im = Image.new("L", (40, 40), 0)
    draw = ImageDraw.Draw(im)
    import math
    cx, cy = 20, 20
    r = 15
    pts = [(int(cx + r * math.cos(2 * math.pi * i / 5 - math.pi / 2)),
            int(cy + r * math.sin(2 * math.pi * i / 5 - math.pi / 2)))
           for i in range(5)]
    draw.polygon(pts, fill=200)
    # Center should be filled
    assert im.getpixel((cx, cy)) == 200


def test_polygon_hexagon():
    im = Image.new("L", (50, 50), 0)
    draw = ImageDraw.Draw(im)
    import math
    cx, cy = 25, 25
    r = 18
    pts = [(int(cx + r * math.cos(2 * math.pi * i / 6)),
            int(cy + r * math.sin(2 * math.pi * i / 6)))
           for i in range(6)]
    draw.polygon(pts, fill=200)
    assert im.getpixel((cx, cy)) == 200


# ---------------------------------------------------------------------------
# polygon() doesn't modify image outside fill area
# ---------------------------------------------------------------------------

def test_polygon_far_pixels_unchanged():
    im = Image.new("L", (50, 50), 50)
    draw = ImageDraw.Draw(im)
    draw.polygon([(10, 10), (20, 10), (20, 20), (10, 20)], fill=200)
    # Pixels far from polygon unchanged
    assert im.getpixel((0, 0)) == 50
    assert im.getpixel((49, 49)) == 50
    assert im.getpixel((30, 30)) == 50


if __name__ == "__main__":
    pytest.main()
