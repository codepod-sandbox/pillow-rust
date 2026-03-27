"""
Tests adapted from upstream Pillow test_image_tobytes.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_tobytes.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_sanity():
    """tobytes returns bytes — from upstream."""
    data = hopper().tobytes()
    assert isinstance(data, bytes)


def test_tobytes_l():
    """L mode: 1 byte per pixel."""
    im = Image.new("L", (10, 10), 200)
    data = im.tobytes()
    assert len(data) == 100
    assert data[0] == 200


def test_tobytes_rgb():
    """RGB mode: 3 bytes per pixel."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    data = im.tobytes()
    assert len(data) == 300
    assert data[0] == 100
    assert data[1] == 150
    assert data[2] == 200


def test_tobytes_rgba():
    """RGBA mode: 4 bytes per pixel."""
    im = Image.new("RGBA", (10, 10), (100, 150, 200, 128))
    data = im.tobytes()
    assert len(data) == 400
    assert data[3] == 128


def test_tobytes_frombytes_roundtrip():
    """tobytes/frombytes roundtrip preserves pixels."""
    im = hopper()
    data = im.tobytes()
    im2 = Image.frombytes("RGB", im.size, data)
    assert im.tobytes() == im2.tobytes()


def test_tobytes_frombytes_l_roundtrip():
    """L mode roundtrip."""
    im = hopper("L")
    data = im.tobytes()
    im2 = Image.frombytes("L", im.size, data)
    assert im.tobytes() == im2.tobytes()


if __name__ == "__main__":
    pytest.main()
