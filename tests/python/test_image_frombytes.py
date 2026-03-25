"""Tests for Image.frombytes(), Image.tobytes(), and raw byte manipulation."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# tobytes() / frombytes() roundtrips
# ---------------------------------------------------------------------------

def test_tobytes_L_length():
    """L image: 1 byte per pixel."""
    im = Image.new("L", (10, 10), 128)
    data = im.tobytes()
    assert len(data) == 100  # 10 * 10


def test_tobytes_RGB_length():
    """RGB image: 3 bytes per pixel."""
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    data = im.tobytes()
    assert len(data) == 300  # 10 * 10 * 3


def test_tobytes_RGBA_length():
    """RGBA image: 4 bytes per pixel."""
    im = Image.new("RGBA", (5, 5), (1, 2, 3, 4))
    data = im.tobytes()
    assert len(data) == 100  # 5 * 5 * 4


def test_tobytes_L_values():
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 200)
    data = im.tobytes()
    assert data[0] == 100
    assert data[1] == 200


def test_tobytes_RGB_values():
    im = Image.new("RGB", (1, 1), (10, 20, 30))
    data = im.tobytes()
    assert data[0] == 10
    assert data[1] == 20
    assert data[2] == 30


def test_frombytes_L():
    raw = bytes([50, 100, 150, 200])
    im = Image.frombytes("L", (4, 1), raw)
    assert im.mode == "L"
    assert im.size == (4, 1)
    assert im.getpixel((0, 0)) == 50
    assert im.getpixel((3, 0)) == 200


def test_frombytes_RGB():
    raw = bytes([10, 20, 30, 40, 50, 60])
    im = Image.frombytes("RGB", (2, 1), raw)
    assert im.mode == "RGB"
    assert im.getpixel((0, 0)) == (10, 20, 30)
    assert im.getpixel((1, 0)) == (40, 50, 60)


def test_frombytes_RGBA():
    raw = bytes([10, 20, 30, 200, 50, 60, 70, 100])
    im = Image.frombytes("RGBA", (2, 1), raw)
    assert im.getpixel((0, 0)) == (10, 20, 30, 200)
    assert im.getpixel((1, 0)) == (50, 60, 70, 100)


def test_frombytes_tobytes_roundtrip_L():
    im = Image.new("L", (8, 8), 0)
    for i in range(64):
        im.putpixel((i % 8, i // 8), i * 4)
    raw = im.tobytes()
    restored = Image.frombytes("L", (8, 8), raw)
    for i in range(64):
        orig = im.getpixel((i % 8, i // 8))
        rest = restored.getpixel((i % 8, i // 8))
        assert orig == rest


def test_frombytes_tobytes_roundtrip_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    raw = im.tobytes()
    restored = Image.frombytes("RGB", (5, 5), raw)
    assert restored.getpixel((2, 2)) == (100, 150, 200)


def test_tobytes_returns_bytes():
    im = Image.new("L", (5, 5), 100)
    assert isinstance(im.tobytes(), (bytes, bytearray))


def test_frombytes_preserves_size():
    raw = bytes(100)
    im = Image.frombytes("L", (10, 10), raw)
    assert im.size == (10, 10)


# ---------------------------------------------------------------------------
# tobytes() changes after putpixel
# ---------------------------------------------------------------------------

def test_tobytes_updates_after_putpixel():
    im = Image.new("L", (4, 1), 0)
    im.putpixel((2, 0), 200)
    data = im.tobytes()
    assert data[2] == 200


if __name__ == "__main__":
    pytest.main()
