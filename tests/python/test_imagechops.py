"""Tests for PIL.ImageChops."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageChops


def test_add():
    im1 = Image.new("L", (10, 10), 100)
    im2 = Image.new("L", (10, 10), 50)
    out = ImageChops.add(im1, im2)
    assert out.getpixel((5, 5)) == 150

def test_add_clamp():
    im1 = Image.new("L", (10, 10), 200)
    im2 = Image.new("L", (10, 10), 200)
    out = ImageChops.add(im1, im2)
    assert out.getpixel((5, 5)) == 255  # clamped

def test_add_modulo():
    im1 = Image.new("L", (10, 10), 200)
    im2 = Image.new("L", (10, 10), 100)
    out = ImageChops.add_modulo(im1, im2)
    assert out.getpixel((5, 5)) == 44  # (200+100) % 256

def test_subtract():
    im1 = Image.new("L", (10, 10), 150)
    im2 = Image.new("L", (10, 10), 50)
    out = ImageChops.subtract(im1, im2)
    assert out.getpixel((5, 5)) == 100

def test_subtract_clamp():
    im1 = Image.new("L", (10, 10), 50)
    im2 = Image.new("L", (10, 10), 200)
    out = ImageChops.subtract(im1, im2)
    assert out.getpixel((5, 5)) == 0  # clamped

def test_multiply():
    im1 = Image.new("L", (10, 10), 128)
    im2 = Image.new("L", (10, 10), 128)
    out = ImageChops.multiply(im1, im2)
    assert out.getpixel((5, 5)) == 64  # 128*128/255 = 64

def test_screen():
    im1 = Image.new("L", (10, 10), 128)
    im2 = Image.new("L", (10, 10), 128)
    out = ImageChops.screen(im1, im2)
    assert out.getpixel((5, 5)) == 191  # 255 - (127*127/255)

def test_difference():
    im1 = Image.new("L", (10, 10), 200)
    im2 = Image.new("L", (10, 10), 50)
    out = ImageChops.difference(im1, im2)
    assert out.getpixel((5, 5)) == 150

def test_lighter():
    im1 = Image.new("L", (10, 10), 100)
    im2 = Image.new("L", (10, 10), 200)
    out = ImageChops.lighter(im1, im2)
    assert out.getpixel((5, 5)) == 200

def test_darker():
    im1 = Image.new("L", (10, 10), 100)
    im2 = Image.new("L", (10, 10), 200)
    out = ImageChops.darker(im1, im2)
    assert out.getpixel((5, 5)) == 100

def test_invert():
    im = Image.new("L", (10, 10), 100)
    out = ImageChops.invert(im)
    assert out.getpixel((5, 5)) == 155

def test_constant():
    im = Image.new("L", (10, 10))
    out = ImageChops.constant(im, 42)
    assert out.getpixel((5, 5)) == 42

def test_duplicate():
    im = Image.new("L", (10, 10), 42)
    out = ImageChops.duplicate(im)
    assert out.getpixel((5, 5)) == 42

def test_offset():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 255)
    out = ImageChops.offset(im, 5, 5)
    assert out.getpixel((5, 5)) == 255
    assert out.getpixel((0, 0)) == 0

def test_rgb_add():
    im1 = Image.new("RGB", (5, 5), (100, 50, 200))
    im2 = Image.new("RGB", (5, 5), (50, 100, 30))
    out = ImageChops.add(im1, im2)
    assert out.getpixel((2, 2)) == (150, 150, 230)

def test_rgb_multiply():
    im1 = Image.new("RGB", (5, 5), (255, 0, 128))
    im2 = Image.new("RGB", (5, 5), (128, 128, 255))
    out = ImageChops.multiply(im1, im2)
    r, g, b = out.getpixel((2, 2))
    assert r == 128  # 255*128/255
    assert g == 0    # 0*128/255
    assert b == 128  # 128*255/255


if __name__ == "__main__":
    pytest.main()
