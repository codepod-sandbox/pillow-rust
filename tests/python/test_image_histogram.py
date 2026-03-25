"""Tests for Image.histogram() — exact counts and distributions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic histogram
# ---------------------------------------------------------------------------

def test_histogram_L_length():
    """L mode histogram has 256 entries."""
    im = Image.new("L", (10, 10), 128)
    h = im.histogram()
    assert len(h) == 256


def test_histogram_L_uniform_all_at_one_bin():
    """Uniform L image: all pixels at one bin."""
    im = Image.new("L", (10, 10), 128)
    h = im.histogram()
    assert h[128] == 100  # 10*10 = 100 pixels
    assert h[0] == 0
    assert h[255] == 0


def test_histogram_L_two_values():
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 200)
    h = im.histogram()
    assert h[50] == 1
    assert h[200] == 1
    assert sum(h) == 2  # total = number of pixels


def test_histogram_L_total_count():
    im = Image.new("L", (30, 20), 100)
    h = im.histogram()
    assert sum(h) == 600  # 30 * 20


def test_histogram_RGB_length():
    """RGB mode histogram has 768 entries (256 per channel)."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    h = im.histogram()
    assert len(h) == 768


def test_histogram_RGB_counts():
    """RGB histogram: each channel has total_pixels in one bin."""
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    h = im.histogram()
    n = 25  # 5 * 5
    # R channel (indices 0-255)
    assert h[10] == n
    # G channel (indices 256-511)
    assert h[256 + 20] == n
    # B channel (indices 512-767)
    assert h[512 + 30] == n


def test_histogram_RGB_total_per_channel():
    im = Image.new("RGB", (4, 5), (0, 0, 0))
    h = im.histogram()
    n = 20  # 4 * 5
    assert sum(h[0:256]) == n
    assert sum(h[256:512]) == n
    assert sum(h[512:768]) == n


def test_histogram_L_full_range():
    """Image with each value 0-255 once has all bins = 1."""
    im = Image.new("L", (256, 1), 0)
    for i in range(256):
        im.putpixel((i, 0), i)
    h = im.histogram()
    assert all(v == 1 for v in h)


def test_histogram_RGBA_length():
    """RGBA histogram has 1024 entries (256 * 4)."""
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 200))
    h = im.histogram()
    assert len(h) == 1024


def test_histogram_1_mode():
    """Mode '1' histogram has 2 entries."""
    im = Image.new("1", (10, 10), 0)
    h = im.histogram()
    assert len(h) == 2
    assert h[0] == 100  # all black pixels


def test_histogram_after_putpixel():
    """histogram reflects putpixel changes."""
    im = Image.new("L", (5, 5), 0)
    im.putpixel((2, 2), 255)
    h = im.histogram()
    assert h[0] == 24  # 24 pixels at 0
    assert h[255] == 1  # 1 pixel at 255


def test_histogram_returns_list_of_ints():
    im = Image.new("L", (5, 5), 100)
    h = im.histogram()
    assert isinstance(h, list)
    assert all(isinstance(v, int) for v in h)


if __name__ == "__main__":
    pytest.main()
