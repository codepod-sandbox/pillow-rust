"""Tests for image.quantize() and image.getcolors()."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


def _make_colorful(w=20, h=20):
    im = Image.new("RGB", (w, h), (0, 0, 0))
    for y in range(h):
        for x in range(w):
            im.putpixel((x, y), (x * 12, y * 12, (x + y) * 6))
    return im


def test_getcolors_rgb():
    im = _make_colorful()
    colors = im.getcolors(500)
    assert colors is not None
    assert len(colors) == 400  # 20x20 unique
    count, color = colors[0]
    assert isinstance(count, int)
    assert isinstance(color, tuple)
    assert len(color) == 3


def test_getcolors_exceeds_max():
    im = _make_colorful()
    result = im.getcolors(5)
    assert result is None


def test_getcolors_l_mode():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 200)
    colors = im.getcolors(256)
    assert len(colors) == 2
    # Most frequent first
    assert colors[0] == (99, 100)
    assert colors[1] == (1, 200)


def test_getcolors_solid():
    im = Image.new("RGB", (5, 5), (42, 42, 42))
    colors = im.getcolors(256)
    assert len(colors) == 1
    assert colors[0] == (25, (42, 42, 42))


def test_quantize_reduces_colors():
    im = _make_colorful()
    q = im.quantize(8)
    assert q.mode == "RGB"
    assert q.size == (20, 20)
    colors = q.getcolors(256)
    assert len(colors) <= 8


def test_quantize_2_colors():
    im = _make_colorful()
    q = im.quantize(2)
    colors = q.getcolors(256)
    assert len(colors) <= 2


def test_quantize_256():
    im = _make_colorful()
    q = im.quantize(256)
    colors = q.getcolors(500)
    assert len(colors) <= 256


def test_quantize_then_convert():
    """Common LLM pattern: quantize then convert back to RGB."""
    im = _make_colorful()
    result = im.quantize(16).convert("RGB")
    assert result.mode == "RGB"


def test_quantize_solid():
    im = Image.new("RGB", (10, 10), (128, 64, 32))
    q = im.quantize(4)
    px = q.getpixel((5, 5))
    # Solid image quantized should stay close to original
    assert abs(px[0] - 128) < 5
    assert abs(px[1] - 64) < 5
    assert abs(px[2] - 32) < 5


def test_quantize_grayscale():
    im = Image.new("L", (10, 10), 100)
    q = im.quantize(4)
    assert q.mode == "RGB"  # quantize always returns RGB


if __name__ == "__main__":
    pytest.main()
