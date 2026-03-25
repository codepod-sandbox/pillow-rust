"""Tests for Image.tobytes() / frombytes() — exact round-trip byte values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# tobytes round-trips
# ---------------------------------------------------------------------------

def test_tobytes_frombytes_L_roundtrip():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((3, 3), 200)
    data = im.tobytes()
    out = Image.frombytes("L", (4, 4), data)
    assert out.getpixel((0, 0)) == 100
    assert out.getpixel((3, 3)) == 200


def test_tobytes_frombytes_RGB_roundtrip():
    im = Image.new("RGB", (4, 4), (0, 0, 0))
    im.putpixel((1, 1), (100, 150, 200))
    data = im.tobytes()
    out = Image.frombytes("RGB", (4, 4), data)
    assert out.getpixel((1, 1)) == (100, 150, 200)


def test_tobytes_frombytes_RGBA_roundtrip():
    im = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    im.putpixel((2, 2), (100, 150, 200, 128))
    data = im.tobytes()
    out = Image.frombytes("RGBA", (4, 4), data)
    r, g, b, a = out.getpixel((2, 2))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 128


# ---------------------------------------------------------------------------
# tobytes length
# ---------------------------------------------------------------------------

def test_tobytes_L_length():
    im = Image.new("L", (10, 10), 0)
    data = im.tobytes()
    assert len(data) == 100  # 10 * 10 * 1 byte per pixel


def test_tobytes_RGB_length():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    data = im.tobytes()
    assert len(data) == 300  # 10 * 10 * 3 bytes per pixel


def test_tobytes_RGBA_length():
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    data = im.tobytes()
    assert len(data) == 400  # 10 * 10 * 4 bytes per pixel


# ---------------------------------------------------------------------------
# tobytes raw values
# ---------------------------------------------------------------------------

def test_tobytes_L_values():
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 10)
    im.putpixel((1, 0), 20)
    im.putpixel((2, 0), 30)
    data = im.tobytes()
    assert data[0] == 10
    assert data[1] == 20
    assert data[2] == 30


def test_tobytes_RGB_values():
    im = Image.new("RGB", (2, 1), (0, 0, 0))
    im.putpixel((0, 0), (10, 20, 30))
    im.putpixel((1, 0), (40, 50, 60))
    data = im.tobytes()
    assert data[0] == 10
    assert data[1] == 20
    assert data[2] == 30
    assert data[3] == 40
    assert data[4] == 50
    assert data[5] == 60


def test_tobytes_all_zeros():
    im = Image.new("L", (5, 5), 0)
    data = im.tobytes()
    assert all(b == 0 for b in data)


def test_tobytes_all_255():
    im = Image.new("L", (5, 5), 255)
    data = im.tobytes()
    assert all(b == 255 for b in data)


# ---------------------------------------------------------------------------
# frombytes validation
# ---------------------------------------------------------------------------

def test_frombytes_uniform_L():
    data = bytes([128] * 25)
    im = Image.frombytes("L", (5, 5), data)
    assert im.getpixel((0, 0)) == 128
    assert im.getpixel((4, 4)) == 128


def test_frombytes_size_preserved():
    data = bytes(100)
    im = Image.frombytes("L", (10, 10), data)
    assert im.size == (10, 10)


def test_frombytes_mode_preserved():
    data = bytes(300)
    im = Image.frombytes("RGB", (10, 10), data)
    assert im.mode == "RGB"


# ---------------------------------------------------------------------------
# tobytes is bytes type
# ---------------------------------------------------------------------------

def test_tobytes_returns_bytes():
    im = Image.new("L", (5, 5), 0)
    data = im.tobytes()
    assert isinstance(data, (bytes, bytearray))


# ---------------------------------------------------------------------------
# Multiple round-trips
# ---------------------------------------------------------------------------

def test_double_roundtrip_preserves_values():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((1, 1), 137)
    # First roundtrip
    d1 = im.tobytes()
    im2 = Image.frombytes("L", (4, 4), d1)
    # Second roundtrip
    d2 = im2.tobytes()
    im3 = Image.frombytes("L", (4, 4), d2)
    assert im3.getpixel((1, 1)) == 137


if __name__ == "__main__":
    pytest.main()
