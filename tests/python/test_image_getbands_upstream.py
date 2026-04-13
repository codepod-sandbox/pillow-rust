"""
Tests adapted from upstream Pillow test_image_getbands.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_getbands.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image


def test_getbands():
    """getbands() returns the correct band names for each mode — from upstream."""
    assert Image.new("L", (1, 1)).getbands() == ("L",)
    assert Image.new("LA", (1, 1)).getbands() == ("L", "A")
    assert Image.new("RGB", (1, 1)).getbands() == ("R", "G", "B")
    assert Image.new("RGBA", (1, 1)).getbands() == ("R", "G", "B", "A")


if __name__ == "__main__":
    pytest.main()
