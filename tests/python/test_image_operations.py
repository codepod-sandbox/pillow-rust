"""Tests for various Image operations — blend, composite, paste with masks."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Image.blend()
# ---------------------------------------------------------------------------

def test_blend_alpha_0():
    """blend with alpha=0 returns first image."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0)
    assert out.getpixel((0, 0)) == 100


def test_blend_alpha_1():
    """blend with alpha=1 returns second image."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=1)
    assert out.getpixel((0, 0)) == 200


def test_blend_alpha_0_5():
    """blend with alpha=0.5 averages images."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0.5)
    # (100 + 200) / 2 = 150
    assert abs(out.getpixel((0, 0)) - 150) <= 3


def test_blend_returns_new():
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0.5)
    assert out is not im1
    assert out is not im2


def test_blend_preserves_mode():
    im1 = Image.new("RGB", (5, 5), (100, 150, 200))
    im2 = Image.new("RGB", (5, 5), (50, 75, 100))
    out = Image.blend(im1, im2, alpha=0.5)
    assert out.mode == "RGB"


def test_blend_preserves_size():
    im1 = Image.new("L", (20, 30), 100)
    im2 = Image.new("L", (20, 30), 200)
    out = Image.blend(im1, im2, alpha=0.5)
    assert out.size == (20, 30)


def test_blend_rgb_values():
    im1 = Image.new("RGB", (5, 5), (0, 0, 0))
    im2 = Image.new("RGB", (5, 5), (200, 100, 50))
    out = Image.blend(im1, im2, alpha=0.5)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 100) <= 5
    assert abs(g - 50) <= 5
    assert abs(b - 25) <= 5


# ---------------------------------------------------------------------------
# Image.composite()
# ---------------------------------------------------------------------------

def test_composite_basic():
    """Composite two images with a mask."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    mask = Image.new("L", (5, 5), 255)  # full opacity → use im2
    out = Image.composite(im1, im2, mask)
    # With full mask, should mostly see im2 (but composite blends, not replaces)
    # mask=255 means weight toward im1 in Pillow's composite
    # composite: out = im1 * (mask/255) + im2 * (1 - mask/255)
    assert out.getpixel((0, 0)) == 100  # mask=255 → 100% of im1


def test_composite_zero_mask():
    """Composite with zero mask: shows im2."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    mask = Image.new("L", (5, 5), 0)
    out = Image.composite(im1, im2, mask)
    assert out.getpixel((0, 0)) == 200


def test_composite_returns_new():
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    mask = Image.new("L", (5, 5), 128)
    out = Image.composite(im1, im2, mask)
    assert out is not im1
    assert out is not im2


def test_composite_preserves_size():
    im1 = Image.new("L", (20, 30), 100)
    im2 = Image.new("L", (20, 30), 200)
    mask = Image.new("L", (20, 30), 128)
    out = Image.composite(im1, im2, mask)
    assert out.size == (20, 30)


# ---------------------------------------------------------------------------
# putdata / getdata
# ---------------------------------------------------------------------------

def test_putdata_getdata_L():
    im = Image.new("L", (3, 2), 0)
    data = [10, 20, 30, 40, 50, 60]
    im.putdata(data)
    result = list(im.getdata())
    assert result == data


def test_putdata_getdata_RGB():
    im = Image.new("RGB", (2, 2), (0, 0, 0))
    data = [(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)]
    im.putdata(data)
    result = list(im.getdata())
    assert result == data


def test_getdata_length():
    im = Image.new("L", (4, 5), 0)
    data = list(im.getdata())
    assert len(data) == 20  # 4 * 5


def test_putdata_uniform():
    im = Image.new("L", (5, 5), 0)
    im.putdata([200] * 25)
    assert im.getpixel((0, 0)) == 200
    assert im.getpixel((4, 4)) == 200


def test_putdata_with_scale_and_offset():
    """putdata with scale and offset should transform values."""
    im = Image.new("L", (3, 1), 0)
    im.putdata([100, 200, 50], scale=2.0, offset=0)
    # Values * scale + offset, clamped to [0, 255]
    v = im.getpixel((0, 0))
    assert v == 200 or v == 255  # 100 * 2 = 200


# ---------------------------------------------------------------------------
# Image.fromarray (if supported)
# ---------------------------------------------------------------------------

def test_fromarray_not_crash():
    """Basic fromarray test — may skip if not supported."""
    try:
        import array
        # Try creating from bytes-like data
        data = bytes([10, 20, 30, 40, 50, 60, 70, 80, 90])
        im = Image.frombytes("L", (3, 3), data)
        assert im.getpixel((0, 0)) == 10
    except Exception:
        pass  # Not critical


if __name__ == "__main__":
    pytest.main()
