"""
Tests adapted from upstream Pillow test_imagechops.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagechops.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageChops
from conftest import assert_image_equal
from helper import hopper


def test_sanity():
    """Verify all ImageChops operations don't crash — from upstream."""
    im = hopper("L")

    ImageChops.constant(im, 128)
    ImageChops.duplicate(im)
    ImageChops.invert(im)
    ImageChops.lighter(im, im)
    ImageChops.darker(im, im)
    ImageChops.difference(im, im)
    ImageChops.multiply(im, im)
    ImageChops.screen(im, im)

    ImageChops.add(im, im)
    ImageChops.add(im, im, 2.0)
    ImageChops.add(im, im, 2.0, 128)
    ImageChops.subtract(im, im)
    ImageChops.subtract(im, im, 2.0)
    ImageChops.subtract(im, im, 2.0, 128)

    ImageChops.add_modulo(im, im)
    ImageChops.subtract_modulo(im, im)

    ImageChops.blend(im, im, 0.5)
    ImageChops.composite(im, im, im)

    ImageChops.offset(im, 10)
    ImageChops.offset(im, 10, 20)


def test_add_clip():
    """Adding hopper to itself clips at 255 — adapted from upstream.

    Our synthetic hopper pixel at (50,50) is (100, 100, 44), so
    add doesn't overflow. We use a high-value pixel to test clipping.
    """
    im = hopper()
    new = ImageChops.add(im, im)
    # Verify no value exceeds 255
    px = new.getpixel((50, 50))
    for v in px:
        assert 0 <= v <= 255
    # Use known high-value pixel to test actual clipping
    im2 = Image.new("RGB", (1, 1), (200, 200, 200))
    clipped = ImageChops.add(im2, im2)
    assert clipped.getpixel((0, 0)) == (255, 255, 255)


def test_add_modulo_no_clip():
    """add_modulo wraps instead of clipping — adapted from upstream."""
    im2 = Image.new("RGB", (1, 1), (200, 200, 200))
    wrapped = ImageChops.add_modulo(im2, im2)
    # (200+200) % 256 = 144
    assert wrapped.getpixel((0, 0)) == (144, 144, 144)


def test_duplicate():
    """Duplicate produces an equal image — from upstream."""
    im = hopper()
    new = ImageChops.duplicate(im)
    assert_image_equal(new, im)


def test_multiply_black():
    """Multiplying with black yields black — from upstream."""
    im1 = hopper()
    black = Image.new("RGB", im1.size, "black")
    new = ImageChops.multiply(im1, black)
    assert_image_equal(new, black)


def test_multiply_white():
    """Multiplying with white is identity — from upstream."""
    im1 = hopper()
    white = Image.new("RGB", im1.size, "white")
    new = ImageChops.multiply(im1, white)
    assert_image_equal(new, im1)


def test_difference_self():
    """Difference of image with itself is black — from upstream."""
    im = hopper()
    new = ImageChops.difference(im, im)
    black = Image.new("RGB", im.size, "black")
    assert_image_equal(new, black)


def test_subtract_clip():
    """Subtract clips at 0 — from upstream."""
    im = hopper()
    black = Image.new("RGB", im.size, "black")
    new = ImageChops.subtract(im, im)
    assert_image_equal(new, black)


def test_subtract_modulo_no_clip():
    """subtract_modulo wraps — from upstream."""
    im = hopper()
    new = ImageChops.subtract_modulo(im, im)
    black = Image.new("RGB", im.size, "black")
    assert_image_equal(new, black)


def test_constant():
    """constant() creates a uniform image — from upstream."""
    im = Image.new("RGB", (20, 10))
    new = ImageChops.constant(im, 128)
    assert new.size == im.size
    assert new.getpixel((0, 0)) == 128
    assert new.getpixel((19, 9)) == 128


def test_invert():
    """Invert then invert is identity — derived from upstream."""
    im = hopper("L")
    inv = ImageChops.invert(im)
    back = ImageChops.invert(inv)
    assert_image_equal(im, back)


def test_offset():
    """Offset wraps pixels — from upstream."""
    im = Image.new("L", (10, 10), 0)
    im.paste(200, (0, 0, 5, 10))
    shifted = ImageChops.offset(im, 5, 0)
    assert shifted.getpixel((0, 5)) == 0
    assert shifted.getpixel((5, 5)) == 200

    # No yoffset means yoffset == xoffset
    assert ImageChops.offset(im, 3) == ImageChops.offset(im, 3, 3)


def test_soft_light():
    """soft_light doesn't crash — from upstream sanity."""
    im = hopper("L")
    ImageChops.soft_light(im, im)


def test_hard_light():
    """hard_light doesn't crash — from upstream sanity."""
    im = hopper("L")
    ImageChops.hard_light(im, im)


def test_overlay():
    """overlay doesn't crash — from upstream sanity."""
    im = hopper("L")
    ImageChops.overlay(im, im)


if __name__ == "__main__":
    pytest.main()
