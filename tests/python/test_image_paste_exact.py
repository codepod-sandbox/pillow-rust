"""Tests for Image.paste() — exact pixel values, masks, and edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic paste
# ---------------------------------------------------------------------------

def test_paste_replaces_pixels():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (4, 4), 200)
    base.paste(patch, (3, 3))
    assert base.getpixel((3, 3)) == 200
    assert base.getpixel((6, 6)) == 200
    # Outside patch stays 0
    assert base.getpixel((2, 2)) == 0
    assert base.getpixel((7, 7)) == 0


def test_paste_at_origin():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 128)
    base.paste(patch, (0, 0))
    assert base.getpixel((0, 0)) == 128
    assert base.getpixel((2, 2)) == 128
    assert base.getpixel((3, 3)) == 0


def test_paste_at_bottom_right():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (3, 3), 99)
    base.paste(patch, (7, 7))
    assert base.getpixel((7, 7)) == 99
    assert base.getpixel((9, 9)) == 99
    assert base.getpixel((6, 6)) == 0


def test_paste_modifies_in_place():
    base = Image.new("L", (10, 10), 0)
    original_id = id(base)
    patch = Image.new("L", (4, 4), 255)
    base.paste(patch, (3, 3))
    assert id(base) == original_id  # paste is in-place


def test_paste_rgb():
    base = Image.new("RGB", (10, 10), (0, 0, 0))
    patch = Image.new("RGB", (3, 3), (100, 150, 200))
    base.paste(patch, (2, 2))
    assert base.getpixel((2, 2)) == (100, 150, 200)
    assert base.getpixel((4, 4)) == (100, 150, 200)
    assert base.getpixel((1, 1)) == (0, 0, 0)


def test_paste_rgba_no_mask():
    """Paste RGBA onto RGB without mask — replaces pixels (ignores alpha)."""
    base = Image.new("RGB", (10, 10), (0, 0, 0))
    patch = Image.new("RGBA", (4, 4), (255, 0, 0, 128))
    base.paste(patch, (3, 3))
    r, g, b = base.getpixel((3, 3))
    # Without mask, direct paste: R channel should be affected
    assert r > 0


# ---------------------------------------------------------------------------
# Paste with color value (not image)
# ---------------------------------------------------------------------------

def test_paste_color_fills_box():
    base = Image.new("L", (10, 10), 0)
    base.paste(200, (2, 2, 6, 6))
    assert base.getpixel((2, 2)) == 200
    assert base.getpixel((5, 5)) == 200
    assert base.getpixel((6, 6)) == 0  # exclusive end
    assert base.getpixel((1, 1)) == 0


def test_paste_rgb_color_fills_box():
    base = Image.new("RGB", (10, 10), (0, 0, 0))
    base.paste((255, 0, 128), (1, 1, 5, 5))
    assert base.getpixel((1, 1)) == (255, 0, 128)
    assert base.getpixel((4, 4)) == (255, 0, 128)
    assert base.getpixel((0, 0)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# Paste with mask
# ---------------------------------------------------------------------------

def test_paste_with_1_mask():
    """Paste with a 1-bit mask: only paste where mask is non-zero."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (4, 4), 200)
    mask = Image.new("1", (4, 4), 0)  # all-zero mask
    # Put some white pixels in mask
    mask.putpixel((1, 1), 255)
    mask.putpixel((2, 2), 255)
    base.paste(patch, (3, 3), mask)
    # Only masked pixels should be pasted
    assert base.getpixel((4, 4)) == 200  # (3+1, 3+1)
    assert base.getpixel((5, 5)) == 200  # (3+2, 3+2)
    assert base.getpixel((3, 3)) == 0    # mask was 0 at (0,0)


def test_paste_with_L_mask_full():
    """Paste with full L mask: all pixels pasted."""
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (4, 4), 200)
    mask = Image.new("L", (4, 4), 255)  # full opacity
    base.paste(patch, (2, 2), mask)
    assert base.getpixel((2, 2)) == 200
    assert base.getpixel((5, 5)) == 200


def test_paste_with_L_mask_none():
    """Paste with empty L mask: no pixels pasted."""
    base = Image.new("L", (10, 10), 50)
    patch = Image.new("L", (4, 4), 200)
    mask = Image.new("L", (4, 4), 0)  # zero opacity
    base.paste(patch, (2, 2), mask)
    # Base unchanged
    assert base.getpixel((2, 2)) == 50
    assert base.getpixel((5, 5)) == 50


def test_paste_with_alpha_mask():
    """Use alpha channel of RGBA image as mask."""
    base = Image.new("RGB", (10, 10), (0, 0, 0))
    patch = Image.new("RGBA", (4, 4), (255, 0, 0, 0))  # fully transparent
    # Extract alpha as mask
    mask = patch.getchannel("A")
    base.paste(patch.convert("RGB"), (3, 3), mask)
    # Should not change base (alpha=0)
    assert base.getpixel((3, 3)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# Paste preserves source image
# ---------------------------------------------------------------------------

def test_paste_does_not_modify_patch():
    base = Image.new("L", (10, 10), 0)
    patch = Image.new("L", (4, 4), 200)
    base.paste(patch, (2, 2))
    # Patch unchanged
    assert patch.getpixel((0, 0)) == 200
    assert patch.size == (4, 4)


# ---------------------------------------------------------------------------
# Paste at specific positions — boundary pixels
# ---------------------------------------------------------------------------

def test_paste_pixel_boundary():
    """Verify the exact boundary pixels are correct after paste."""
    base = Image.new("L", (20, 20), 0)
    patch = Image.new("L", (6, 6), 150)
    base.paste(patch, (5, 5))
    # Edge pixels of patch
    assert base.getpixel((5, 5)) == 150    # top-left of patch
    assert base.getpixel((10, 5)) == 150   # top-right of patch
    assert base.getpixel((5, 10)) == 150   # bottom-left of patch
    assert base.getpixel((10, 10)) == 150  # bottom-right of patch
    # One pixel outside
    assert base.getpixel((4, 4)) == 0
    assert base.getpixel((11, 11)) == 0


if __name__ == "__main__":
    pytest.main()
