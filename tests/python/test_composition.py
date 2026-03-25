"""Tests for Image.blend, composite, alpha_composite, getdata, putdata, point."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# blend
# ---------------------------------------------------------------------------

def test_blend_half():
    im1 = Image.new("RGB", (10, 10), (0, 0, 0))
    im2 = Image.new("RGB", (10, 10), (200, 200, 200))
    out = Image.blend(im1, im2, 0.5)
    r, g, b = out.getpixel((5, 5))
    assert 95 <= r <= 105

def test_blend_zero():
    im1 = Image.new("RGB", (10, 10), (100, 0, 0))
    im2 = Image.new("RGB", (10, 10), (0, 200, 0))
    out = Image.blend(im1, im2, 0.0)
    assert out.getpixel((5, 5)) == (100, 0, 0)

def test_blend_one():
    im1 = Image.new("RGB", (10, 10), (100, 0, 0))
    im2 = Image.new("RGB", (10, 10), (0, 200, 0))
    out = Image.blend(im1, im2, 1.0)
    assert out.getpixel((5, 5)) == (0, 200, 0)


# ---------------------------------------------------------------------------
# composite
# ---------------------------------------------------------------------------

def test_composite_mask_white():
    im1 = Image.new("RGB", (10, 10), (255, 0, 0))
    im2 = Image.new("RGB", (10, 10), (0, 255, 0))
    mask = Image.new("L", (10, 10), 255)
    out = Image.composite(im1, im2, mask)
    px = out.getpixel((5, 5))
    # Pillow: mask=255 selects im1 (red)
    assert px[:3] == (255, 0, 0)

def test_composite_mask_black():
    im1 = Image.new("RGB", (10, 10), (255, 0, 0))
    im2 = Image.new("RGB", (10, 10), (0, 255, 0))
    mask = Image.new("L", (10, 10), 0)
    out = Image.composite(im1, im2, mask)
    px = out.getpixel((5, 5))
    # Pillow: mask=0 selects im2 (green)
    assert px[:3] == (0, 255, 0)


# ---------------------------------------------------------------------------
# alpha_composite
# ---------------------------------------------------------------------------

def test_alpha_composite_opaque():
    dst = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    src = Image.new("RGBA", (10, 10), (0, 255, 0, 255))
    dst.alpha_composite(src)  # in-place, returns None
    assert dst.getpixel((5, 5)) == (0, 255, 0, 255)

def test_alpha_composite_transparent():
    dst = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    src = Image.new("RGBA", (10, 10), (0, 255, 0, 0))
    dst.alpha_composite(src)  # in-place, returns None
    assert dst.getpixel((5, 5)) == (255, 0, 0, 255)


# ---------------------------------------------------------------------------
# getdata / putdata
# ---------------------------------------------------------------------------

def test_getdata_L():
    im = Image.new("L", (3, 3), 42)
    data = im.getdata()
    assert len(data) == 9
    assert data[0] == 42

def test_getdata_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))
    data = im.getdata()
    assert len(data) == 4
    assert data[0] == (10, 20, 30)

def test_putdata_L():
    im = Image.new("L", (3, 3), 0)
    im.putdata([100] * 9)
    assert im.getpixel((1, 1)) == 100

def test_putdata_RGB():
    im = Image.new("RGB", (2, 2), (0, 0, 0))
    im.putdata([(255, 0, 0)] * 4)
    assert im.getpixel((0, 0)) == (255, 0, 0)


# ---------------------------------------------------------------------------
# point
# ---------------------------------------------------------------------------

def test_point_identity():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    lut = list(range(256))
    out = im.point(lut)
    assert out.getpixel((5, 5)) == (100, 150, 200)

def test_point_invert():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    lut = [255 - i for i in range(256)]
    out = im.point(lut)
    assert out.getpixel((5, 5)) == (155, 105, 55)

def test_point_callable():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    out = im.point(lambda x: min(x * 2, 255))
    assert out.getpixel((5, 5)) == (200, 200, 200)


if __name__ == "__main__":
    pytest.main()
