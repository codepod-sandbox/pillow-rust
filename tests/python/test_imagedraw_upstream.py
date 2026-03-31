"""
Tests adapted from upstream Pillow test_imagedraw.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagedraw.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageDraw
from helper import hopper


def test_sanity():
    """Basic ImageDraw operations run without error — from upstream."""
    im = hopper("RGB").copy()

    draw = ImageDraw.ImageDraw(im)
    draw = ImageDraw.Draw(im)

    draw.ellipse(list(range(4)))
    draw.line(list(range(10)))
    draw.polygon(list(range(100)))
    draw.rectangle(list(range(4)))


def test_draw_rgba():
    """Draw on RGBA image — from upstream sanity."""
    im = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([25, 25, 75, 75], fill=(0, 0, 255, 128))
    assert im.getpixel((50, 50)) == (0, 0, 255, 128)


def test_draw_line_basic():
    """Draw a line and verify a pixel changed — derived from upstream."""
    im = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(im)
    draw.line([(10, 10), (90, 10)], fill=(0, 0, 0), width=1)
    # Pixel on the line should be black
    assert im.getpixel((50, 10)) == (0, 0, 0)


def test_draw_rectangle_basic():
    """Draw a rectangle and verify fill pixel — derived from upstream."""
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([25, 25, 75, 75], fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)


def test_draw_ellipse_basic():
    """Draw a filled ellipse — derived from upstream."""
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.ellipse([25, 25, 75, 75], fill=(255, 0, 0))
    # Center should be filled
    assert im.getpixel((50, 50)) == (255, 0, 0)


def test_draw_on_l():
    """Draw on L mode image — from upstream."""
    im = Image.new("L", (100, 100), 255)
    draw = ImageDraw.Draw(im)
    draw.rectangle([25, 25, 75, 75], fill=0)
    assert im.getpixel((50, 50)) == 0


def test_draw_point():
    """Draw a point and verify pixel — derived from upstream."""
    im = Image.new("RGB", (10, 10), "white")
    draw = ImageDraw.Draw(im)
    draw.point((5, 5), fill=(255, 0, 0))
    assert im.getpixel((5, 5)) == (255, 0, 0)


def test_draw_arc_basic():
    """Draw an arc without error — from upstream."""
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.arc([25, 25, 75, 75], 0, 180)


def test_draw_chord_basic():
    """Draw a chord without error — from upstream."""
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.chord([25, 25, 75, 75], 0, 180, fill=(0, 128, 0))


def test_draw_pieslice_basic():
    """Draw a pieslice without error — from upstream."""
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.pieslice([25, 25, 75, 75], 0, 180, fill=(255, 255, 0))


if __name__ == "__main__":
    pytest.main()
