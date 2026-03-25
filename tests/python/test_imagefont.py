"""Tests for PIL.ImageFont."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageFont


# -- load_default -----------------------------------------------------------

def test_load_default():
    font = ImageFont.load_default()
    assert font is not None
    assert hasattr(font, "getbbox")


def test_load_default_with_size():
    font = ImageFont.load_default(size=16)
    assert font is not None
    assert font.size == 16


# -- truetype ---------------------------------------------------------------

def test_truetype():
    font = ImageFont.truetype("arial.ttf", 12)
    assert font is not None
    assert font.size == 12


def test_truetype_different_sizes():
    f1 = ImageFont.truetype("arial.ttf", 10)
    f2 = ImageFont.truetype("arial.ttf", 20)
    assert f1.size == 10
    assert f2.size == 20


# -- load -------------------------------------------------------------------

def test_load():
    font = ImageFont.load("some_font.pil")
    assert font is not None


# -- getbbox ----------------------------------------------------------------

def test_getbbox():
    font = ImageFont.load_default()
    bbox = font.getbbox("Hello")
    assert len(bbox) == 4
    x0, y0, x1, y1 = bbox
    assert x0 == 0
    assert y0 <= 0  # top of text (negative = above origin)
    assert x1 > 0  # width
    assert y1 > y0  # height


def test_getbbox_empty():
    font = ImageFont.load_default()
    bbox = font.getbbox("")
    assert bbox[2] == 0  # zero width for empty text


# -- getlength --------------------------------------------------------------

def test_getlength():
    font = ImageFont.load_default()
    length = font.getlength("Hello")
    assert length > 0


def test_getlength_longer_text():
    font = ImageFont.load_default()
    l1 = font.getlength("Hi")
    l2 = font.getlength("Hello World")
    assert l2 > l1


# -- getsize ----------------------------------------------------------------

def test_getsize():
    font = ImageFont.load_default()
    size = font.getsize("Hello")
    assert len(size) == 2
    w, h = size
    assert w > 0
    assert h > 0


# -- getmetrics -------------------------------------------------------------

def test_getmetrics():
    font = ImageFont.load_default()
    metrics = font.getmetrics()
    assert len(metrics) == 2
    ascent, descent = metrics
    assert ascent > 0
    assert descent >= 0


# -- rendering with font ---------------------------------------------------

def test_draw_text_with_font():
    im = Image.new("RGB", (100, 30), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    draw.text((5, 5), "Hi", fill=(0, 0, 0), font=font)
    # Verify some pixels changed (text drawn)
    # Check that not everything is still white
    found_dark = False
    for y in range(30):
        for x in range(100):
            px = im.getpixel((x, y))
            if px[0] < 128:
                found_dark = True
                break
        if found_dark:
            break
    assert found_dark, "text should have drawn dark pixels"


if __name__ == "__main__":
    pytest.main()
