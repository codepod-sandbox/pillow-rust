"""Tests for ImageOps.flip, mirror, grayscale, colorize, invert."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageOps


# ---------------------------------------------------------------------------
# flip() — vertical flip
# ---------------------------------------------------------------------------

def test_flip_moves_top_to_bottom():
    im = Image.new("L", (5, 4), 0)
    # Put a white row at top
    for x in range(5):
        im.putpixel((x, 0), 255)
    out = ImageOps.flip(im)
    # Top row should now be 0, bottom row should be 255
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((0, 3)) == 255


def test_flip_double_returns_original():
    im = Image.new("L", (5, 5), 0)
    im.putpixel((2, 0), 200)
    out = ImageOps.flip(ImageOps.flip(im))
    assert out.getpixel((2, 0)) == 200
    assert out.getpixel((2, 4)) == 0


def test_flip_preserves_mode():
    for mode, color in [("RGB", (100, 150, 200)), ("L", 100), ("RGBA", (1, 2, 3, 4))]:
        im = Image.new(mode, (5, 5), color)
        out = ImageOps.flip(im)
        assert out.mode == mode


def test_flip_preserves_size():
    im = Image.new("RGB", (30, 20), (0, 0, 0))
    out = ImageOps.flip(im)
    assert out.size == (30, 20)


def test_flip_rgb_exact():
    im = Image.new("RGB", (3, 2), 0)
    im.putpixel((1, 0), (100, 150, 200))  # top row
    im.putpixel((1, 1), (10, 20, 30))    # bottom row
    out = ImageOps.flip(im)
    assert out.getpixel((1, 0)) == (10, 20, 30)    # was bottom
    assert out.getpixel((1, 1)) == (100, 150, 200)  # was top


# ---------------------------------------------------------------------------
# mirror() — horizontal flip
# ---------------------------------------------------------------------------

def test_mirror_moves_left_to_right():
    im = Image.new("L", (5, 5), 0)
    im.putpixel((0, 2), 255)
    out = ImageOps.mirror(im)
    assert out.getpixel((4, 2)) == 255
    assert out.getpixel((0, 2)) == 0


def test_mirror_double_returns_original():
    im = Image.new("L", (6, 6), 0)
    im.putpixel((0, 3), 128)
    out = ImageOps.mirror(ImageOps.mirror(im))
    assert out.getpixel((0, 3)) == 128


def test_mirror_preserves_mode():
    for mode, color in [("RGB", (100, 150, 200)), ("L", 100)]:
        im = Image.new(mode, (5, 5), color)
        out = ImageOps.mirror(im)
        assert out.mode == mode


def test_mirror_rgb_exact():
    im = Image.new("RGB", (3, 3), 0)
    im.putpixel((0, 1), (200, 100, 50))
    im.putpixel((2, 1), (10, 20, 30))
    out = ImageOps.mirror(im)
    assert out.getpixel((2, 1)) == (200, 100, 50)
    assert out.getpixel((0, 1)) == (10, 20, 30)


# ---------------------------------------------------------------------------
# grayscale()
# ---------------------------------------------------------------------------

def test_grayscale_produces_L_mode():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageOps.grayscale(im)
    assert out.mode == "L"


def test_grayscale_L_input_passthrough():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.grayscale(im)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


def test_grayscale_luma_formula():
    """BT.601 luma for (100, 150, 200)."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageOps.grayscale(im)
    expected = (100 * 19595 + 150 * 38470 + 200 * 7471 + 0x8000) >> 16
    val = out.getpixel((0, 0))
    assert abs(int(val) - expected) <= 1


def test_grayscale_white():
    im = Image.new("RGB", (5, 5), (255, 255, 255))
    out = ImageOps.grayscale(im)
    assert out.getpixel((0, 0)) == 255


def test_grayscale_black():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    out = ImageOps.grayscale(im)
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# invert()
# ---------------------------------------------------------------------------

def test_invert_L_255_minus_v():
    im = Image.new("L", (4, 1), 0)
    vals = [0, 100, 200, 255]
    for i, v in enumerate(vals):
        im.putpixel((i, 0), v)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 255
    assert out.getpixel((1, 0)) == 155
    assert out.getpixel((2, 0)) == 55
    assert out.getpixel((3, 0)) == 0


def test_invert_double_returns_original():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.invert(ImageOps.invert(im))
    assert out.getpixel((0, 0)) == 128


def test_invert_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageOps.invert(im)
    r, g, b = out.getpixel((0, 0))
    assert r == 155
    assert g == 105
    assert b == 55


def test_invert_preserves_mode():
    for mode, color in [("L", 100), ("RGB", (100, 150, 200))]:
        im = Image.new(mode, (5, 5), color)
        out = ImageOps.invert(im)
        assert out.mode == mode


# ---------------------------------------------------------------------------
# colorize()
# ---------------------------------------------------------------------------

def test_colorize_black_to_color():
    """Black pixels map to 'black' color."""
    im = Image.new("L", (5, 5), 0)
    out = ImageOps.colorize(im, black=(255, 0, 0), white=(0, 0, 255))
    r, g, b = out.getpixel((0, 0))
    assert r == 255
    assert g == 0
    assert b == 0


def test_colorize_white_to_color():
    """White pixels map to 'white' color."""
    im = Image.new("L", (5, 5), 255)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(255, 128, 0))
    r, g, b = out.getpixel((0, 0))
    assert r == 255
    assert g == 128
    assert b == 0


def test_colorize_produces_RGB():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.colorize(im, black="black", white="white")
    assert out.mode == "RGB"


def test_colorize_midpoint():
    """Midpoint (128) should be halfway between black and white colors."""
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.colorize(im, black=(0, 0, 0), white=(200, 200, 200))
    r, g, b = out.getpixel((0, 0))
    # ~50% between 0 and 200 → ~100 (allow some rounding)
    assert 95 <= r <= 105
    assert 95 <= g <= 105
    assert 95 <= b <= 105


if __name__ == "__main__":
    pytest.main()
