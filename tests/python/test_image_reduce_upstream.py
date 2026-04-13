"""
Tests adapted from upstream Pillow test_image_reduce.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_reduce.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image


def test_args_factor_scalar():
    """reduce() with scalar factor uses ceiling division — from upstream."""
    im = Image.new("L", (10, 10))
    assert (4, 4) == im.reduce(3).size


def test_args_factor_tuple_horizontal():
    """reduce() with (fx, fy) tuple — from upstream."""
    im = Image.new("L", (10, 10))
    assert (4, 10) == im.reduce((3, 1)).size


def test_args_factor_tuple_vertical():
    """reduce() with (1, fy) tuple — from upstream."""
    im = Image.new("L", (10, 10))
    assert (10, 4) == im.reduce((1, 3)).size


def test_args_factor_error_zero():
    """reduce() with factor 0 raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(0)
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_factor_error_float():
    """reduce() with float factor raises TypeError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2.0)
        raise AssertionError("Expected TypeError")
    except TypeError:
        pass


def test_args_factor_error_zero_in_tuple():
    """reduce() with (0, n) tuple raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce((0, 10))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_full():
    """reduce() with full-image box produces correct size — from upstream."""
    im = Image.new("L", (10, 10))
    assert (5, 5) == im.reduce(2, (0, 0, 10, 10)).size


def test_args_box_single_pixel():
    """reduce() with 1x1 box produces (1,1) — from upstream."""
    im = Image.new("L", (10, 10))
    assert (1, 1) == im.reduce(2, (5, 5, 6, 6)).size


def test_args_box_error_out_of_bounds_x():
    """reduce() with x1 > width raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (0, 0, 11, 10))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_error_out_of_bounds_y():
    """reduce() with y1 > height raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (0, 0, 10, 11))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_error_negative_x():
    """reduce() with x0 < 0 raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (-1, 0, 10, 10))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_error_negative_y():
    """reduce() with y0 < 0 raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (0, -1, 10, 10))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_error_zero_height():
    """reduce() with y0 == y1 raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (0, 5, 10, 5))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_args_box_error_zero_width():
    """reduce() with x0 == x1 raises ValueError — from upstream."""
    im = Image.new("L", (10, 10))
    try:
        im.reduce(2, (5, 0, 5, 10))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_reduce_L_mode():
    """reduce() on L mode image returns correct mode and size — derived from upstream."""
    im = Image.new("L", (20, 20), 128)
    result = im.reduce(2)
    assert result.mode == "L"
    assert result.size == (10, 10)


def test_reduce_RGB_mode():
    """reduce() on RGB mode image returns correct mode and size — derived from upstream."""
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    result = im.reduce(2)
    assert result.mode == "RGB"
    assert result.size == (10, 10)


if __name__ == "__main__":
    pytest.main()
