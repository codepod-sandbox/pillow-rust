"""Tests for PIL.ImageColor."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import ImageColor


# ---------------------------------------------------------------------------
# getrgb — named colors
# ---------------------------------------------------------------------------

def test_named_red():
    assert ImageColor.getrgb("red") == (255, 0, 0)

def test_named_blue():
    assert ImageColor.getrgb("blue") == (0, 0, 255)

def test_named_white():
    assert ImageColor.getrgb("white") == (255, 255, 255)

def test_named_black():
    assert ImageColor.getrgb("black") == (0, 0, 0)

def test_named_case_insensitive():
    assert ImageColor.getrgb("Red") == (255, 0, 0)
    assert ImageColor.getrgb("RED") == (255, 0, 0)
    assert ImageColor.getrgb("DarkSlateGray") == (47, 79, 79)

def test_named_grey_alias():
    assert ImageColor.getrgb("gray") == ImageColor.getrgb("grey")

# ---------------------------------------------------------------------------
# getrgb — hex
# ---------------------------------------------------------------------------

def test_hex_6():
    assert ImageColor.getrgb("#ff0000") == (255, 0, 0)
    assert ImageColor.getrgb("#00FF00") == (0, 255, 0)

def test_hex_3():
    assert ImageColor.getrgb("#f00") == (255, 0, 0)
    assert ImageColor.getrgb("#0f0") == (0, 255, 0)

def test_hex_8():
    assert ImageColor.getrgb("#ff000080") == (255, 0, 0, 128)

def test_hex_4():
    assert ImageColor.getrgb("#f008") == (255, 0, 0, 136)

# ---------------------------------------------------------------------------
# getrgb — rgb() / rgba()
# ---------------------------------------------------------------------------

def test_rgb_func():
    assert ImageColor.getrgb("rgb(255, 0, 0)") == (255, 0, 0)

def test_rgba_func():
    assert ImageColor.getrgb("rgba(255, 0, 0, 128)") == (255, 0, 0, 128)

# ---------------------------------------------------------------------------
# getrgb — hsl()
# ---------------------------------------------------------------------------

def test_hsl_red():
    r, g, b = ImageColor.getrgb("hsl(0, 100%, 50%)")
    assert r == 255
    assert g == 0
    assert b == 0

def test_hsl_green():
    r, g, b = ImageColor.getrgb("hsl(120, 100%, 50%)")
    assert g == 255

def test_hsl_gray():
    r, g, b = ImageColor.getrgb("hsl(0, 0%, 50%)")
    assert r == g == b == 128

# ---------------------------------------------------------------------------
# getrgb — errors
# ---------------------------------------------------------------------------

def test_unknown_color():
    with pytest.raises(ValueError):
        ImageColor.getrgb("notacolor")

def test_non_string():
    with pytest.raises(ValueError):
        ImageColor.getrgb(123)

# ---------------------------------------------------------------------------
# getcolor
# ---------------------------------------------------------------------------

def test_getcolor_rgb():
    assert ImageColor.getcolor("red", "RGB") == (255, 0, 0)

def test_getcolor_rgba():
    assert ImageColor.getcolor("red", "RGBA") == (255, 0, 0, 255)

def test_getcolor_rgba_with_alpha():
    assert ImageColor.getcolor("#ff000080", "RGBA") == (255, 0, 0, 128)

def test_getcolor_l():
    val = ImageColor.getcolor("white", "L")
    assert val == 255

def test_getcolor_l_black():
    val = ImageColor.getcolor("black", "L")
    assert val == 0

# ---------------------------------------------------------------------------
# colormap
# ---------------------------------------------------------------------------

def test_colormap_exists():
    assert len(ImageColor.colormap) > 140

def test_colormap_values_are_hex():
    for name, val in ImageColor.colormap.items():
        assert val.startswith("#"), f"{name}: {val}"
        assert len(val) == 7, f"{name}: {val}"


if __name__ == "__main__":
    pytest.main()
