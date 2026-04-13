"""
Tests adapted from upstream Pillow test_image_entropy.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_entropy.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_entropy_L():
    """entropy() on a non-trivial L image is positive — from upstream."""
    im = hopper("L")
    assert im.entropy() > 0


def test_entropy_RGB():
    """entropy() on a non-trivial RGB image is positive — from upstream."""
    im = hopper("RGB")
    assert im.entropy() > 0


def test_entropy_RGBA():
    """entropy() on a non-trivial RGBA image is positive — derived from upstream."""
    im = hopper("RGBA")
    assert im.entropy() > 0


def test_entropy_uniform_is_zero():
    """entropy() on a single-colour image is 0.0 — from upstream."""
    im = Image.new("L", (100, 100), 128)
    assert im.entropy() == 0.0


def test_entropy_two_colors():
    """entropy() on a two-colour half-and-half image is 1.0 — from upstream."""
    im = Image.new("L", (2, 1))
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 255)
    # Two equally-likely values: entropy = 1 bit
    assert abs(im.entropy() - 1.0) < 1e-9


def test_entropy_mask():
    """entropy() with a mask restricts computation to masked region — from upstream."""
    im = Image.new("L", (10, 10), 128)
    mask = Image.new("L", (10, 10), 0)
    # Masked region is all-zero → uniform → entropy 0
    assert im.entropy(mask=mask) == 0.0


if __name__ == "__main__":
    pytest.main()
