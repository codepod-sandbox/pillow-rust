"""
Tests adapted from upstream Pillow test_image_histogram.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_histogram.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from helper import hopper


def test_histogram():
    """Verify histogram shape across modes — from upstream."""
    def histogram(mode):
        h = hopper(mode).histogram()
        return len(h), min(h), max(h)

    l_len, l_min, l_max = histogram("L")
    assert l_len == 256
    assert l_min == 0
    assert l_max > 0

    rgb_len, rgb_min, rgb_max = histogram("RGB")
    assert rgb_len == 768
    assert rgb_min >= 0

    rgba_len, rgba_min, rgba_max = histogram("RGBA")
    assert rgba_len == 1024
    assert rgba_min >= 0


if __name__ == "__main__":
    pytest.main()
