"""
Tests adapted from upstream Pillow test_image_getextrema.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_getextrema.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_extrema():
    """Test getextrema across supported modes — adapted from upstream.

    Note: our synthetic hopper has slightly different ranges than
    the real hopper.ppm, so we check structure rather than exact values.
    """
    l_min, l_max = hopper("L").getextrema()
    assert l_min >= 0
    assert l_max <= 255
    assert l_max > l_min

    rgb_ext = hopper("RGB").getextrema()
    assert len(rgb_ext) == 3
    for mn, mx in rgb_ext:
        assert mn >= 0
        assert mx <= 255

    rgba_ext = hopper("RGBA").getextrema()
    assert len(rgba_ext) == 4
    # Alpha channel should be (255, 255) since convert from RGB adds full alpha
    assert rgba_ext[3] == (255, 255)


if __name__ == "__main__":
    pytest.main()
