"""Stress tests — larger images, many operations, edge conditions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance, ImageChops


def test_large_image_operations():
    im = Image.new("RGB", (500, 500), (100, 150, 200))
    gray = im.convert("L")
    resized = gray.resize((250, 250))
    cropped = resized.crop((50, 50, 200, 200))
    assert cropped.size == (150, 150)


def test_many_putpixels():
    im = Image.new("L", (100, 100), 0)
    for x in range(100):
        for y in range(100):
            im.putpixel((x, y), (x + y) % 256)
    assert im.getpixel((50, 50)) == 100


def test_many_pastes():
    base = Image.new("L", (100, 100), 0)
    tile = Image.new("L", (10, 10), 200)
    for x in range(0, 100, 10):
        for y in range(0, 100, 10):
            base.paste(tile, (x, y))
    assert base.getpixel((55, 55)) == 200


def test_chain_10_resizes():
    im = Image.new("L", (1000, 1000), 128)
    for _ in range(10):
        w, h = im.size
        im = im.resize((max(1, w // 2), max(1, h // 2)))
    assert im.size[0] >= 1
    assert im.size[1] >= 1


def test_chain_filters():
    im = Image.new("L", (30, 30), 100)
    for _ in range(5):
        im = im.filter(ImageFilter.BLUR)
    assert im.getpixel((15, 15)) == 100


def test_chain_enhancers():
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    for _ in range(3):
        im = ImageEnhance.Brightness(im).enhance(1.0)
        im = ImageEnhance.Contrast(im).enhance(1.0)
    px = im.getpixel((10, 10))
    assert px == (100, 150, 200)


def test_split_merge_many_times():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    for _ in range(5):
        bands = im.split()
        im = Image.merge("RGB", bands)
    assert im.getpixel((5, 5)) == (100, 150, 200)


def test_copy_many_times():
    im = Image.new("L", (10, 10), 42)
    for _ in range(10):
        im = im.copy()
    assert im.getpixel((5, 5)) == 42


def test_tobytes_frombytes_many():
    im = Image.new("L", (50, 50), 128)
    for _ in range(5):
        data = im.tobytes()
        im = Image.frombytes("L", (50, 50), data)
    assert im.getpixel((25, 25)) == 128


def test_draw_many_shapes():
    im = Image.new("L", (100, 100), 0)
    draw = ImageDraw.Draw(im)
    for i in range(20):
        x = (i * 5) % 90
        draw.rectangle([(x, x), (x + 10, x + 10)], fill=200)
    assert im.size == (100, 100)


def test_chops_chain():
    im1 = Image.new("L", (10, 10), 100)
    im2 = Image.new("L", (10, 10), 50)
    result = ImageChops.add(im1, im2)
    result = ImageChops.subtract(result, im2)
    result = ImageChops.multiply(result, im1)
    assert result.size == (10, 10)


if __name__ == "__main__":
    pytest.main()
