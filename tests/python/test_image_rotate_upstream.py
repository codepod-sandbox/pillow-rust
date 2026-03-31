"""
Tests adapted from upstream Pillow test_image_rotate.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_rotate.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_mode():
    """rotate preserves mode — from upstream test_mode."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        out = im.rotate(45)
        assert out.mode == mode
        assert out.size == im.size  # no expand: size unchanged


def test_zero():
    """rotate on zero-size image — from upstream test_zero."""
    im = Image.new("RGB", (0, 0))
    for angle in (0, 45, 90, 180, 270):
        out = im.rotate(angle)
        assert out.mode == im.mode
        assert out.size == im.size


def test_center():
    """rotate with center/translate parameters runs without error — from upstream."""
    im = hopper()
    out = im.rotate(45, center=(0, 0))
    assert out.mode == im.mode
    out = im.rotate(45, translate=(im.size[0] // 2, 0))
    assert out.mode == im.mode
    out = im.rotate(45, center=(0, 0), translate=(im.size[0] // 2, 0))
    assert out.mode == im.mode


def test_alpha_rotate_no_fill():
    """RGBA rotation with expand gives transparent corners — from upstream."""
    im = Image.new("RGBA", (10, 10), "green")
    im = im.rotate(45, expand=1)
    corner = im.getpixel((0, 0))
    assert corner == (0, 0, 0, 0)


def test_alpha_rotate_with_fill():
    """RGBA rotation with fillcolor fills corners — from upstream."""
    im = Image.new("RGBA", (10, 10), "green")
    im = im.rotate(45, expand=1, fillcolor=(255, 0, 0, 255))
    corner = im.getpixel((0, 0))
    assert corner == (255, 0, 0, 255)


def test_angle_180_double_identity():
    """Rotate 180 then 180 is identity — derived from upstream."""
    im = hopper()
    out = im.rotate(180).rotate(180)
    assert_image_equal(im, out)


def test_angle_90_quadruple_identity():
    """Rotate 90 four times is identity — derived from upstream."""
    im = Image.new("RGB", (10, 20), "blue")
    out = im.rotate(90, expand=1).rotate(90, expand=1).rotate(90, expand=1).rotate(90, expand=1)
    assert_image_equal(im, out)


if __name__ == "__main__":
    pytest.main()
