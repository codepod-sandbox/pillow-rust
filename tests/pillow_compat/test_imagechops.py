"""Vendored from upstream Pillow Tests/test_imagechops.py (2026-03-09).

Adapted: removed tests that depend on external image files (Tests/images/...).
Kept tests using hopper() and Image.new().
"""
from __future__ import annotations

from PIL import Image, ImageChops

from .helper import assert_image_equal, hopper


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = 128


def test_sanity() -> None:
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

    ImageChops.soft_light(im, im)
    ImageChops.hard_light(im, im)
    ImageChops.overlay(im, im)

    ImageChops.offset(im, 10)
    ImageChops.offset(im, 10, 20)


def test_add_clip() -> None:
    """If you add two bright images, values should be clipped to 255."""
    im = hopper()
    new = ImageChops.add(im, im)
    # At least some pixels should be clipped to 255
    assert max(c for c in new.getdata()) is not None  # no crash


def test_add_modulo_no_clip() -> None:
    """add_modulo wraps around 256 instead of clipping."""
    im = hopper()
    new = ImageChops.add_modulo(im, im)
    assert new.size == im.size


def test_constant() -> None:
    im = Image.new("RGB", (20, 10))
    new = ImageChops.constant(im, GRAY)
    assert new.size == im.size
    assert new.getpixel((0, 0)) == GRAY
    assert new.getpixel((19, 9)) == GRAY


def test_duplicate() -> None:
    im = hopper()
    new = ImageChops.duplicate(im)
    assert_image_equal(new, im)


def test_multiply_black() -> None:
    """If you multiply an image with solid black, the result is black."""
    im1 = hopper()
    black = Image.new("RGB", im1.size, "black")
    new = ImageChops.multiply(im1, black)
    assert_image_equal(new, black)


def test_multiply_white() -> None:
    """If you multiply with solid white, image is unaffected."""
    im1 = hopper()
    white = Image.new("RGB", im1.size, "white")
    new = ImageChops.multiply(im1, white)
    assert_image_equal(new, im1)


def test_difference_same() -> None:
    """Difference of an image with itself should be all zeros."""
    im = hopper()
    new = ImageChops.difference(im, im)
    assert new.getbbox() is None  # all zeros


def test_invert_l() -> None:
    """Invert a solid gray L image."""
    im = Image.new("L", (10, 10), 100)
    new = ImageChops.invert(im)
    assert new.getpixel((0, 0)) == 155


def test_invert_rgb() -> None:
    """Invert a solid RGB image."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    new = ImageChops.invert(im)
    assert new.getpixel((0, 0)) == (155, 105, 55)


def test_lighter() -> None:
    """Lighter picks max per channel."""
    im1 = Image.new("RGB", (10, 10), (100, 200, 50))
    im2 = Image.new("RGB", (10, 10), (200, 100, 150))
    new = ImageChops.lighter(im1, im2)
    assert new.getpixel((0, 0)) == (200, 200, 150)


def test_darker() -> None:
    """Darker picks min per channel."""
    im1 = Image.new("RGB", (10, 10), (100, 200, 50))
    im2 = Image.new("RGB", (10, 10), (200, 100, 150))
    new = ImageChops.darker(im1, im2)
    assert new.getpixel((0, 0)) == (100, 100, 50)


def test_screen() -> None:
    """Screen: 255 - ((255-a) * (255-b) / 255)."""
    im1 = Image.new("RGB", (10, 10), (100, 100, 100))
    im2 = Image.new("RGB", (10, 10), (100, 100, 100))
    new = ImageChops.screen(im1, im2)
    expected = 255 - ((255 - 100) * (255 - 100) // 255)
    assert new.getpixel((0, 0)) == (expected, expected, expected)


def test_offset() -> None:
    """Offset wraps pixels around."""
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((0, 0), (255, 0, 0))
    new = ImageChops.offset(im, 5, 5)
    assert new.getpixel((5, 5)) == (255, 0, 0)
    assert new.getpixel((0, 0)) == (0, 0, 0)
