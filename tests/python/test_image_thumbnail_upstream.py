"""Tests for Image.thumbnail() — aspect-ratio-preserving resize."""

from PIL import Image


def test_thumbnail_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    im.thumbnail((100, 100))
    assert im.size == (100, 50)
    assert im.getpixel((0, 0)) == (255, 0, 0)


def test_thumbnail_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    im.thumbnail((100, 100))
    assert im.size == (50, 100)
    assert im.getpixel((0, 0)) == (0, 255, 0)


def test_thumbnail_square():
    im = Image.new("RGB", (200, 200), (0, 0, 255))
    im.thumbnail((100, 100))
    assert im.size == (100, 100)


def test_thumbnail_already_smaller():
    im = Image.new("RGB", (50, 30))
    im.thumbnail((100, 100))
    assert im.size == (50, 30)  # unchanged


def test_thumbnail_exact_fit():
    im = Image.new("RGB", (100, 100))
    im.thumbnail((100, 100))
    assert im.size == (100, 100)


def test_thumbnail_L_mode():
    im = Image.new("L", (200, 100), 128)
    im.thumbnail((50, 50))
    assert im.size == (50, 25)
    assert im.mode == "L"


def test_thumbnail_RGBA_mode():
    im = Image.new("RGBA", (200, 100), (255, 0, 0, 128))
    im.thumbnail((50, 50))
    assert im.size == (50, 25)
    assert im.mode == "RGBA"


def test_thumbnail_modifies_in_place():
    im = Image.new("RGB", (200, 100))
    original_id = id(im)
    im.thumbnail((100, 100))
    assert id(im) == original_id  # same object


def test_thumbnail_non_square_target():
    im = Image.new("RGB", (400, 200))
    im.thumbnail((200, 50))
    # Must fit in 200x50: 400/200=2, 200/50=4, scale by 4
    assert im.size == (100, 50)
