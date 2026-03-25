"""Tests for ImageDraw shape drawing — exact pixel verification."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw


def _white(size=(50, 50), mode="L"):
    return Image.new(mode, size, 255 if mode == "L" else (255, 255, 255))


def _black(size=(50, 50), mode="L"):
    return Image.new(mode, size, 0)


# ---------------------------------------------------------------------------
# line()
# ---------------------------------------------------------------------------

def test_line_horizontal():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (20, 10)], fill=200)
    # Middle of line
    assert im.getpixel((12, 10)) == 200
    # Outside line
    assert im.getpixel((12, 11)) == 0


def test_line_vertical():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.line([(10, 5), (10, 20)], fill=200)
    assert im.getpixel((10, 12)) == 200
    assert im.getpixel((11, 12)) == 0


def test_line_rgb():
    im = _black(mode="RGB")
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (20, 10)], fill=(255, 0, 0))
    assert im.getpixel((12, 10)) == (255, 0, 0)


def test_line_single_point():
    """A line to itself draws a single pixel."""
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.line([(10, 10), (10, 10)], fill=200)
    assert im.getpixel((10, 10)) == 200


def test_line_does_not_overflow():
    """Line within bounds doesn't affect outside pixels."""
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (10, 5)], fill=200)
    assert im.getpixel((4, 5)) == 0
    assert im.getpixel((11, 5)) == 0


# ---------------------------------------------------------------------------
# rectangle()
# ---------------------------------------------------------------------------

def test_rectangle_outline():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.rectangle([(5, 5), (15, 15)], outline=200)
    # Corners should be drawn
    assert im.getpixel((5, 5)) == 200
    assert im.getpixel((15, 15)) == 200
    # Interior should be black (no fill)
    assert im.getpixel((10, 10)) == 0


def test_rectangle_fill():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.rectangle([(5, 5), (15, 15)], fill=200)
    assert im.getpixel((10, 10)) == 200
    # Outside rect
    assert im.getpixel((4, 4)) == 0
    assert im.getpixel((16, 16)) == 0


def test_rectangle_fill_and_outline():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.rectangle([(5, 5), (15, 15)], fill=150, outline=255)
    # Outline
    assert im.getpixel((5, 5)) == 255
    # Interior
    assert im.getpixel((10, 10)) == 150


def test_rectangle_single_pixel():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (10, 10)], fill=200)
    assert im.getpixel((10, 10)) == 200


def test_rectangle_rgb_fill():
    im = _black(mode="RGB")
    draw = ImageDraw.Draw(im)
    draw.rectangle([(5, 5), (15, 15)], fill=(100, 150, 200))
    assert im.getpixel((10, 10)) == (100, 150, 200)


def test_rectangle_does_not_modify_outside():
    im = Image.new("L", (50, 50), 100)
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (20, 20)], fill=0)
    # Outside stays at 100
    assert im.getpixel((9, 9)) == 100
    assert im.getpixel((21, 21)) == 100


# ---------------------------------------------------------------------------
# ellipse()
# ---------------------------------------------------------------------------

def test_ellipse_center_filled():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.ellipse([(5, 5), (20, 20)], fill=200)
    # Center of ellipse should be filled
    cx, cy = 12, 12
    assert im.getpixel((cx, cy)) == 200


def test_ellipse_outside_not_filled():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.ellipse([(10, 10), (20, 20)], fill=200)
    # Far outside corners should be 0
    assert im.getpixel((0, 0)) == 0
    assert im.getpixel((49, 49)) == 0


def test_ellipse_outline():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.ellipse([(5, 5), (20, 20)], outline=200)
    # The ellipse outline should have some non-zero pixels in the bounding region
    # Check that at least one pixel in the expected ellipse region is drawn
    found = False
    cx, cy = 12, 12
    for y in range(5, 8):
        for x in range(9, 17):
            if im.getpixel((x, y)) == 200:
                found = True
                break
        if found:
            break
    assert found, "Expected ellipse outline pixels near top of ellipse"


def test_ellipse_rgb():
    im = _black(mode="RGB")
    draw = ImageDraw.Draw(im)
    draw.ellipse([(5, 5), (20, 20)], fill=(255, 0, 128))
    cx, cy = 12, 12
    assert im.getpixel((cx, cy)) == (255, 0, 128)


def test_circle_is_symmetric():
    """A circle should be symmetric left-right."""
    im = _black(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(5, 5), (35, 35)], fill=200)
    # Check symmetry: (10, 20) and (30, 20) should both be filled
    assert im.getpixel((10, 20)) == 200
    assert im.getpixel((30, 20)) == 200


# ---------------------------------------------------------------------------
# polygon()
# ---------------------------------------------------------------------------

def test_polygon_triangle_center():
    im = _black(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 35), (20, 5), (35, 35)], fill=200)
    # Centroid roughly at (20, 25)
    assert im.getpixel((20, 25)) == 200


def test_polygon_rectangle_as_polygon():
    im = _black()
    draw = ImageDraw.Draw(im)
    draw.polygon([(10, 10), (20, 10), (20, 20), (10, 20)], fill=200)
    assert im.getpixel((15, 15)) == 200
    assert im.getpixel((9, 9)) == 0


def test_polygon_outline_color():
    im = _black(size=(40, 40))
    draw = ImageDraw.Draw(im)
    draw.polygon([(5, 5), (35, 5), (35, 35), (5, 35)], outline=200)
    # Top edge
    assert im.getpixel((20, 5)) == 200


# ---------------------------------------------------------------------------
# fill=0 should work (black fill, not default)
# ---------------------------------------------------------------------------

def test_rectangle_fill_0_is_black():
    im = Image.new("L", (20, 20), 255)
    draw = ImageDraw.Draw(im)
    draw.rectangle([(5, 5), (15, 15)], fill=0)
    assert im.getpixel((10, 10)) == 0


def test_line_fill_0_is_black():
    im = Image.new("L", (20, 20), 255)
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (15, 10)], fill=0)
    assert im.getpixel((10, 10)) == 0


def test_ellipse_fill_0_is_black():
    im = Image.new("L", (20, 20), 255)
    draw = ImageDraw.Draw(im)
    draw.ellipse([(5, 5), (15, 15)], fill=0)
    assert im.getpixel((10, 10)) == 0


if __name__ == "__main__":
    pytest.main()
