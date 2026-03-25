"""Tests for Image.info dict, format, mode, size attributes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# info dict
# ---------------------------------------------------------------------------

def test_info_default_empty():
    """New images have an empty info dict."""
    im = Image.new("RGB", (5, 5), 0)
    assert isinstance(im.info, dict)
    assert len(im.info) == 0


def test_info_set_custom():
    im = Image.new("RGB", (5, 5), 0)
    im.info["dpi"] = (72, 72)
    assert im.info["dpi"] == (72, 72)


def test_info_preserved_after_copy():
    im = Image.new("RGB", (5, 5), 0)
    im.info["key"] = "value"
    cp = im.copy()
    assert cp.info.get("key") == "value"


def test_info_not_shared_between_copies():
    im = Image.new("RGB", (5, 5), 0)
    im.info["x"] = 1
    cp = im.copy()
    cp.info["x"] = 99
    assert im.info["x"] == 1  # original unchanged


def test_info_independent_between_new_images():
    a = Image.new("RGB", (5, 5), 0)
    b = Image.new("RGB", (5, 5), 0)
    a.info["k"] = "a"
    assert "k" not in b.info


# ---------------------------------------------------------------------------
# format attribute
# ---------------------------------------------------------------------------

def test_format_default_none():
    """New images have format=None."""
    im = Image.new("RGB", (5, 5), 0)
    assert im.format is None


# ---------------------------------------------------------------------------
# mode attribute
# ---------------------------------------------------------------------------

def test_mode_L():
    im = Image.new("L", (5, 5), 0)
    assert im.mode == "L"


def test_mode_RGB():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    assert im.mode == "RGB"


def test_mode_RGBA():
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    assert im.mode == "RGBA"


def test_mode_LA():
    im = Image.new("LA", (5, 5), (0, 255))
    assert im.mode == "LA"


def test_mode_1():
    im = Image.new("1", (5, 5), 0)
    assert im.mode == "1"


# ---------------------------------------------------------------------------
# size, width, height attributes
# ---------------------------------------------------------------------------

def test_size_returns_tuple():
    im = Image.new("RGB", (10, 20), 0)
    assert im.size == (10, 20)


def test_width_height():
    im = Image.new("RGB", (30, 40), 0)
    assert im.width == 30
    assert im.height == 40


def test_size_equals_width_height():
    im = Image.new("L", (15, 25), 0)
    assert im.size == (im.width, im.height)


def test_size_1x1():
    im = Image.new("L", (1, 1), 128)
    assert im.size == (1, 1)
    assert im.width == 1
    assert im.height == 1


def test_size_wide():
    im = Image.new("L", (1000, 1), 0)
    assert im.size == (1000, 1)
    assert im.width == 1000


def test_size_tall():
    im = Image.new("L", (1, 1000), 0)
    assert im.size == (1, 1000)
    assert im.height == 1000


# ---------------------------------------------------------------------------
# copy() preserves all attributes
# ---------------------------------------------------------------------------

def test_copy_mode_preserved():
    for mode, color in [("L", 100), ("RGB", (1, 2, 3)), ("RGBA", (1, 2, 3, 4))]:
        im = Image.new(mode, (5, 5), color)
        cp = im.copy()
        assert cp.mode == mode


def test_copy_size_preserved():
    im = Image.new("RGB", (30, 20), 0)
    cp = im.copy()
    assert cp.size == (30, 20)


def test_copy_pixel_values_preserved():
    im = Image.new("RGB", (3, 3), (100, 150, 200))
    im.putpixel((1, 1), (50, 75, 100))
    cp = im.copy()
    assert cp.getpixel((1, 1)) == (50, 75, 100)
    assert cp.getpixel((0, 0)) == (100, 150, 200)


def test_copy_is_independent():
    im = Image.new("L", (5, 5), 100)
    cp = im.copy()
    cp.putpixel((0, 0), 200)
    assert im.getpixel((0, 0)) == 100  # original unchanged


if __name__ == "__main__":
    pytest.main()
