"""Tests for Image.getdata() and putdata() — adapted from upstream Pillow."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# getdata()
# ---------------------------------------------------------------------------

def test_getdata_L():
    im = Image.new("L", (4, 4), 100)
    data = im.getdata()
    assert len(data) == 16
    assert all(v == 100 for v in data)


def test_getdata_L_integer_values():
    """L-mode pixels should be plain integers."""
    im = Image.new("L", (3, 3), 200)
    data = im.getdata()
    assert isinstance(data[0], int)
    assert data[0] == 200


def test_getdata_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))
    data = im.getdata()
    assert len(data) == 4
    assert data[0] == (10, 20, 30)


def test_getdata_RGB_tuple_type():
    """RGB pixels should be tuples."""
    im = Image.new("RGB", (3, 3), (100, 150, 200))
    data = im.getdata()
    assert isinstance(data[0], tuple)
    assert len(data[0]) == 3


def test_getdata_RGBA():
    im = Image.new("RGBA", (2, 2), (10, 20, 30, 200))
    data = im.getdata()
    assert len(data) == 4
    assert data[0] == (10, 20, 30, 200)


def test_getdata_RGBA_tuple_length():
    """RGBA pixels should be 4-tuples."""
    im = Image.new("RGBA", (3, 3), (1, 2, 3, 4))
    data = im.getdata()
    assert isinstance(data[0], tuple)
    assert len(data[0]) == 4


def test_getdata_LA():
    im = Image.new("LA", (2, 2), (100, 200))
    data = im.getdata()
    assert len(data) == 4
    assert data[0] == (100, 200)


def test_getdata_row_major_order():
    """getdata() returns pixels in row-major (left-to-right, top-to-bottom) order."""
    im = Image.new("L", (3, 2), 0)
    im.putpixel((0, 0), 10)
    im.putpixel((1, 0), 20)
    im.putpixel((2, 0), 30)
    im.putpixel((0, 1), 40)
    im.putpixel((1, 1), 50)
    im.putpixel((2, 1), 60)
    data = im.getdata()
    assert list(data) == [10, 20, 30, 40, 50, 60]


def test_getdata_rgb_row_major():
    """RGB getdata in row order."""
    im = Image.new("RGB", (2, 2), (0, 0, 0))
    im.putpixel((0, 0), (1, 2, 3))
    im.putpixel((1, 0), (4, 5, 6))
    im.putpixel((0, 1), (7, 8, 9))
    im.putpixel((1, 1), (10, 11, 12))
    data = im.getdata()
    assert list(data) == [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]


# ---------------------------------------------------------------------------
# putdata()
# ---------------------------------------------------------------------------

def test_putdata_L_list():
    im = Image.new("L", (4, 1), 0)
    im.putdata([10, 20, 30, 40])
    assert im.getpixel((0, 0)) == 10
    assert im.getpixel((1, 0)) == 20
    assert im.getpixel((2, 0)) == 30
    assert im.getpixel((3, 0)) == 40


def test_putdata_RGB_tuples():
    im = Image.new("RGB", (2, 1), 0)
    im.putdata([(100, 150, 200), (50, 75, 100)])
    assert im.getpixel((0, 0)) == (100, 150, 200)
    assert im.getpixel((1, 0)) == (50, 75, 100)


def test_putdata_RGBA_tuples():
    im = Image.new("RGBA", (2, 1), 0)
    im.putdata([(100, 150, 200, 255), (50, 75, 100, 128)])
    assert im.getpixel((0, 0)) == (100, 150, 200, 255)
    assert im.getpixel((1, 0)) == (50, 75, 100, 128)


def test_putdata_roundtrip_L():
    """getdata → putdata → getdata should produce same values."""
    im = Image.new("L", (5, 5), 0)
    for i in range(25):
        im.putpixel((i % 5, i // 5), i * 10)
    data = im.getdata()
    im2 = Image.new("L", (5, 5), 0)
    im2.putdata(data)
    assert list(im2.getdata()) == list(data)


def test_putdata_roundtrip_RGB():
    """getdata → putdata → getdata should produce same RGB values."""
    im = Image.new("RGB", (4, 4), 0)
    for y in range(4):
        for x in range(4):
            im.putpixel((x, y), (x * 60, y * 60, (x + y) * 30))
    data = im.getdata()
    im2 = Image.new("RGB", (4, 4), 0)
    im2.putdata(list(data))
    assert list(im2.getdata()) == list(data)


def test_putdata_clamps_to_255():
    """Values > 255 should be clamped (treated as modulo 256 via & 0xFF)."""
    im = Image.new("L", (2, 1), 0)
    im.putdata([300, 256])  # 300 & 0xFF = 44, 256 & 0xFF = 0
    # Values get &0xFF, so 300 → 44, 256 → 0
    d = im.getdata()
    assert d[0] == 44
    assert d[1] == 0


# ---------------------------------------------------------------------------
# frombytes / tobytes roundtrip
# ---------------------------------------------------------------------------

def test_tobytes_L():
    im = Image.new("L", (4, 1), 0)
    im.putpixel((0, 0), 10)
    im.putpixel((1, 0), 20)
    im.putpixel((2, 0), 30)
    im.putpixel((3, 0), 40)
    data = im.tobytes()
    assert isinstance(data, bytes)
    assert len(data) == 4
    assert data[0] == 10
    assert data[3] == 40


def test_tobytes_RGB_length():
    im = Image.new("RGB", (4, 4), (100, 150, 200))
    data = im.tobytes()
    assert len(data) == 4 * 4 * 3


def test_tobytes_RGBA_length():
    im = Image.new("RGBA", (3, 3), (1, 2, 3, 4))
    data = im.tobytes()
    assert len(data) == 3 * 3 * 4


def test_frombytes_roundtrip_L():
    """frombytes(mode, size, tobytes()) should reconstruct the image."""
    im = Image.new("L", (5, 5), 0)
    for i in range(5):
        im.putpixel((i, i), i * 50)
    raw = im.tobytes()
    im2 = Image.frombytes("L", (5, 5), raw)
    assert im2.tobytes() == raw


def test_frombytes_roundtrip_RGB():
    im = Image.new("RGB", (4, 4), (0, 0, 0))
    for y in range(4):
        for x in range(4):
            im.putpixel((x, y), (x * 80, y * 80, 100))
    raw = im.tobytes()
    im2 = Image.frombytes("RGB", (4, 4), raw)
    assert im2.tobytes() == raw


if __name__ == "__main__":
    pytest.main()
