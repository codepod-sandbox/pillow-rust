"""Regression tests — verify specific behaviors don't break."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageOps


def test_new_rgb_default_is_black():
    im = Image.new("RGB", (5, 5))
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_new_l_default_is_zero():
    im = Image.new("L", (5, 5))
    assert im.getpixel((0, 0)) == 0


def test_crop_returns_new_image():
    im = Image.new("L", (10, 10), 100)
    cropped = im.crop((2, 2, 8, 8))
    assert cropped is not im


def test_resize_returns_new_image():
    im = Image.new("L", (10, 10), 100)
    resized = im.resize((5, 5))
    assert resized is not im


def test_rotate_returns_new_image():
    im = Image.new("L", (10, 10), 100)
    rotated = im.rotate(90)
    assert rotated is not im


def test_convert_returns_new_image():
    im = Image.new("L", (10, 10), 100)
    converted = im.convert("RGB")
    assert converted is not im


def test_filter_returns_new_image():
    from PIL import ImageFilter
    im = Image.new("L", (10, 10), 100)
    filtered = im.filter(ImageFilter.BLUR)
    assert filtered is not im


def test_point_returns_new_image():
    im = Image.new("L", (10, 10), 100)
    pointed = im.point(lambda x: x)
    assert pointed is not im


def test_paste_modifies_in_place():
    im = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (5, 5), 200)
    original_id = id(im)
    im.paste(patch, (0, 0))
    assert id(im) == original_id


def test_putpixel_modifies_in_place():
    im = Image.new("L", (10, 10), 0)
    original_id = id(im)
    im.putpixel((5, 5), 200)
    assert id(im) == original_id


def test_thumbnail_modifies_in_place():
    im = Image.new("L", (100, 100), 128)
    original_id = id(im)
    im.thumbnail((50, 50))
    assert id(im) == original_id


def test_getbands_matches_mode():
    assert Image.new("L", (1, 1)).getbands() == ("L",)
    assert Image.new("RGB", (1, 1)).getbands() == ("R", "G", "B")
    assert Image.new("RGBA", (1, 1)).getbands() == ("R", "G", "B", "A")


def test_width_height_match_size():
    im = Image.new("L", (30, 40))
    assert im.width == im.size[0] == 30
    assert im.height == im.size[1] == 40


def test_format_is_none_for_new():
    im = Image.new("L", (5, 5))
    assert im.format is None


def test_invert_then_invert_identity():
    im = Image.new("L", (5, 5), 123)
    out = ImageOps.invert(ImageOps.invert(im))
    assert out.getpixel((0, 0)) == 123


def test_draw_on_new_image():
    im = Image.new("RGB", (50, 50))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (40, 40)], fill=(255, 0, 0))
    assert im.getpixel((25, 25)) == (255, 0, 0)


if __name__ == "__main__":
    pytest.main()
