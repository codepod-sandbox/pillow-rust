"""Tests for ImageDraw.polygon()."""

from PIL import Image, ImageDraw


def test_polygon_triangle_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(50, 10), (10, 90), (90, 90)], fill=(255, 0, 0))
    # Center of triangle should be filled
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Outside should be black
    assert im.getpixel((5, 5)) == (0, 0, 0)


def test_polygon_rectangle_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], fill=(0, 255, 0))
    assert im.getpixel((50, 50)) == (0, 255, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_polygon_outline_only():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], outline=(0, 0, 255))
    # Edge should be drawn
    assert im.getpixel((20, 20)) == (0, 0, 255)
    assert im.getpixel((50, 20)) == (0, 0, 255)
    # Interior should be empty
    assert im.getpixel((50, 50)) == (0, 0, 0)


def test_polygon_flat_coords():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([20, 20, 80, 20, 80, 80, 20, 80], fill=(128, 128, 128))
    assert im.getpixel((50, 50)) == (128, 128, 128)


def test_polygon_fill_and_outline():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)],
                 fill=(255, 0, 0), outline=(0, 255, 0))
    # Interior should be fill color
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Edge should be outline color
    assert im.getpixel((20, 20)) == (0, 255, 0)


def test_polygon_pentagon():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(50, 10), (90, 40), (75, 85), (25, 85), (10, 40)],
                 fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_polygon_L_mode():
    im = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], fill=200)
    assert im.getpixel((50, 50)) == 200
