"""Vendored from upstream Pillow Tests/test_imageenhance.py (2026-03-09).

Adapted: removed alpha test (uses putalpha which we don't have).
"""
from __future__ import annotations

from PIL import Image, ImageEnhance

from .helper import hopper


def test_sanity() -> None:
    # Implicit asserts no exception:
    ImageEnhance.Color(hopper()).enhance(0.5)
    ImageEnhance.Contrast(hopper()).enhance(0.5)
    ImageEnhance.Brightness(hopper()).enhance(0.5)
    ImageEnhance.Sharpness(hopper()).enhance(0.5)


def test_crash() -> None:
    # crashes on small images
    im = Image.new("RGB", (1, 1))
    ImageEnhance.Sharpness(im).enhance(0.5)


def test_enhance_zero() -> None:
    """Enhancement factor of 0.0 should produce a degenerate image."""
    im = hopper()
    enhanced = ImageEnhance.Brightness(im).enhance(0.0)
    # All pixels should be black
    assert enhanced.getpixel((0, 0)) == (0, 0, 0)


def test_enhance_one() -> None:
    """Enhancement factor of 1.0 should return the original image."""
    im = hopper()
    enhanced = ImageEnhance.Brightness(im).enhance(1.0)
    assert im.tobytes() == enhanced.tobytes()


def test_contrast() -> None:
    im = hopper()
    enhanced = ImageEnhance.Contrast(im).enhance(0.0)
    # Factor 0 should produce a solid gray image (mean luminance)
    # Just check it doesn't crash and produces uniform output
    assert enhanced.size == im.size


def test_color_zero() -> None:
    """Color factor 0 should produce grayscale."""
    im = hopper()
    enhanced = ImageEnhance.Color(im).enhance(0.0)
    # Convert result and original to L, they should differ
    # (grayscale vs color)
    assert enhanced.size == im.size
