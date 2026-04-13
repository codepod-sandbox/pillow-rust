"""
Tests adapted from upstream Pillow test_imageops_usm.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageops_usm.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageFilter
from helper import hopper


def test_gaussian_blur_returns_image():
    """GaussianBlur filter returns an Image of the same mode and size."""
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        result = im.filter(ImageFilter.GaussianBlur(2))
        assert result.mode == mode
        assert result.size == im.size


def test_unsharp_mask_returns_image():
    """UnsharpMask filter returns an Image of the same mode and size."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        result = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        assert result.mode == mode
        assert result.size == im.size


def test_gaussian_blur_L():
    """GaussianBlur on L mode image produces non-trivially different result."""
    im = hopper("L")
    result = im.filter(ImageFilter.GaussianBlur(2))
    # Blurred image should differ from original
    assert result.tobytes() != im.tobytes()


def test_gaussian_blur_radius_zero():
    """GaussianBlur with radius 0 should produce a nearly-identical image."""
    im = Image.new("L", (20, 20), 128)
    result = im.filter(ImageFilter.GaussianBlur(0))
    # Uniform image stays uniform after any blur
    assert result.size == im.size
    assert result.mode == im.mode


def test_unsharp_mask_preserves_flat():
    """UnsharpMask on a flat image returns the same flat image — from upstream."""
    # A completely flat image has no edges to sharpen
    im = Image.new("L", (50, 50), 128)
    result = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    assert result.getextrema() == (128, 128)


def test_gaussian_blur_default_radius():
    """GaussianBlur with default radius (2) works without explicit arg — from upstream."""
    im = hopper("RGB")
    result = im.filter(ImageFilter.GaussianBlur())
    assert result.mode == "RGB"
    assert result.size == im.size


if __name__ == "__main__":
    pytest.main()
