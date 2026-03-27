"""
Tests adapted from upstream Pillow test_imagecolor.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagecolor.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageColor


def test_hash():
    """Test hex color parsing — from upstream test_hash."""
    # short 3 components
    assert (255, 0, 0) == ImageColor.getrgb("#f00")
    assert (0, 255, 0) == ImageColor.getrgb("#0f0")
    assert (0, 0, 255) == ImageColor.getrgb("#00f")

    # long 3 components
    assert (222, 0, 0) == ImageColor.getrgb("#de0000")
    assert (0, 222, 0) == ImageColor.getrgb("#00de00")
    assert (0, 0, 222) == ImageColor.getrgb("#0000de")

    # case insensitivity
    assert ImageColor.getrgb("#DEF") == ImageColor.getrgb("#def")
    assert ImageColor.getrgb("#DEFDEF") == ImageColor.getrgb("#defdef")

    # not a number
    with pytest.raises(ValueError):
        ImageColor.getrgb("#fo0")
    with pytest.raises(ValueError):
        ImageColor.getrgb("#fo0000")

    # wrong number of components
    with pytest.raises(ValueError):
        ImageColor.getrgb("#f0000")
    with pytest.raises(ValueError):
        ImageColor.getrgb("#f000000")


def test_colormap():
    """Test named color lookups — from upstream test_colormap."""
    assert (0, 0, 0) == ImageColor.getrgb("black")
    assert (255, 255, 255) == ImageColor.getrgb("white")
    assert (255, 255, 255) == ImageColor.getrgb("WHITE")

    with pytest.raises(ValueError):
        ImageColor.getrgb("black ")


def test_functions():
    """Test rgb() and rgba() function syntax — from upstream test_functions."""
    # rgb numbers
    assert (255, 0, 0) == ImageColor.getrgb("rgb(255,0,0)")
    assert (0, 255, 0) == ImageColor.getrgb("rgb(0,255,0)")
    assert (0, 0, 255) == ImageColor.getrgb("rgb(0,0,255)")

    # percents
    assert (255, 0, 0) == ImageColor.getrgb("rgb(100%,0%,0%)")
    assert (0, 255, 0) == ImageColor.getrgb("rgb(0%,100%,0%)")
    assert (0, 0, 255) == ImageColor.getrgb("rgb(0%,0%,100%)")

    # hsl
    assert (255, 0, 0) == ImageColor.getrgb("hsl(0,100%,50%)")
    assert (255, 0, 0) == ImageColor.getrgb("hsl(360,100%,50%)")
    assert (0, 255, 255) == ImageColor.getrgb("hsl(180,100%,50%)")

    # hsv
    assert (255, 0, 0) == ImageColor.getrgb("hsv(0,100%,100%)")
    assert (255, 0, 0) == ImageColor.getrgb("hsv(360,100%,100%)")
    assert (0, 255, 255) == ImageColor.getrgb("hsv(180,100%,100%)")

    # case insensitivity
    assert ImageColor.getrgb("RGB(255,0,0)") == ImageColor.getrgb("rgb(255,0,0)")
    assert ImageColor.getrgb("HSL(0,100%,50%)") == ImageColor.getrgb("hsl(0,100%,50%)")

    # space agnosticism
    assert (255, 0, 0) == ImageColor.getrgb("rgb(  255  ,  0  ,  0  )")

    # wrong number of components
    with pytest.raises(ValueError):
        ImageColor.getrgb("rgb(255,0)")
    with pytest.raises(ValueError):
        ImageColor.getrgb("rgb(255,0,0,0)")


def test_rounding_errors():
    """Verify getcolor L matches Image.new convert — from upstream."""
    for color in ("red", "green", "blue", "white", "black", "yellow", "cyan"):
        expected = Image.new("RGB", (1, 1), color).convert("L").getpixel((0, 0))
        actual = ImageColor.getcolor(color, "L")
        assert expected == actual

    assert (0, 0, 0, 255) == ImageColor.getcolor("black", "RGBA")
    assert (255, 255, 255, 255) == ImageColor.getcolor("white", "RGBA")

    assert 0 == ImageColor.getcolor("black", "L")
    assert 255 == ImageColor.getcolor("white", "L")


if __name__ == "__main__":
    pytest.main()
