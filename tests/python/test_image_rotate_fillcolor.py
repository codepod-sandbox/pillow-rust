"""
Tests for Image.rotate() fillcolor and RGBA transparency, adapted from:

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_rotate.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

from PIL import Image
from conftest import assert_image


# ---------------------------------------------------------------------------
# fillcolor — matches upstream test_rotate_with_fill / test_alpha_rotate_*
# ---------------------------------------------------------------------------


def test_rotate_rgb_no_fill():
    """RGB rotation without fillcolor: corners default to black."""
    im = Image.new("RGB", (20, 20), "green")
    out = im.rotate(45)
    assert out.mode == "RGB"
    assert out.size == (20, 20)
    # Corner should be black (default fill)
    assert out.getpixel((0, 0)) == (0, 0, 0)


def test_rotate_rgb_with_fill():
    """RGB rotation with fillcolor: empty areas use that colour."""
    im = Image.new("RGB", (20, 20), "green")
    out = im.rotate(45, fillcolor="blue")
    assert out.mode == "RGB"
    assert out.size == (20, 20)
    assert out.getpixel((0, 0)) == (0, 0, 255)


def test_rotate_rgb_with_fill_tuple():
    """fillcolor accepts an RGB tuple."""
    im = Image.new("RGB", (20, 20), (0, 200, 0))
    out = im.rotate(45, fillcolor=(255, 0, 0))
    assert out.getpixel((0, 0)) == (255, 0, 0)


def test_rotate_rgb_with_fill_white():
    """fillcolor='white' fills corners with white."""
    im = Image.new("RGB", (20, 20), "green")
    out = im.rotate(45, fillcolor="white")
    assert out.getpixel((0, 0)) == (255, 255, 255)


def test_alpha_rotate_no_fill():
    """Upstream: RGBA corners without fillcolor should be transparent.

    Mirrors test_alpha_rotate_no_fill from Pillow's test_image_rotate.py.
    """
    im = Image.new("RGBA", (10, 10), "green")
    out = im.rotate(45, expand=True)
    corner = out.getpixel((0, 0))
    assert corner == (0, 0, 0, 0), f"expected transparent corner, got {corner}"


def test_alpha_rotate_with_fill():
    """Upstream: RGBA corners with fillcolor should be that colour.

    Mirrors test_alpha_rotate_with_fill from Pillow's test_image_rotate.py.
    """
    im = Image.new("RGBA", (10, 10), "green")
    out = im.rotate(45, expand=True, fillcolor=(255, 0, 0, 255))
    corner = out.getpixel((0, 0))
    assert corner == (255, 0, 0, 255), f"expected red corner, got {corner}"


def test_rotate_fillcolor_preserves_mode():
    """Output mode must match input mode when fillcolor is used."""
    for mode in ("L", "RGB", "RGBA"):
        im = Image.new(mode, (20, 20))
        fc = 128 if mode == "L" else (128, 64, 32)
        if mode == "RGBA":
            fc = (128, 64, 32, 255)
        out = im.rotate(45, fillcolor=fc)
        assert out.mode == mode, f"mode changed for {mode}"


def test_rotate_fillcolor_center_pixel_unchanged():
    """Centre pixel of a filled solid image should survive rotation."""
    im = Image.new("RGB", (20, 20), (0, 200, 0))
    out = im.rotate(45, fillcolor=(255, 0, 0))
    # Centre pixel should still be the original green
    cx, cy = 10, 10
    assert out.getpixel((cx, cy)) == (0, 200, 0)


def test_rotate_no_fillcolor_explicit_none():
    """Explicit fillcolor=None should behave like omitting the parameter."""
    im = Image.new("RGB", (20, 20), "green")
    out1 = im.rotate(45)
    out2 = im.rotate(45, fillcolor=None)
    assert out1.tobytes() == out2.tobytes()
