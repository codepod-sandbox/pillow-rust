"""
Tests for Image error handling, validation, and edge cases.

Tests adapted from upstream Pillow test suites.
The Pillow licence (MIT-CMU) applies to ported test logic.
"""

import pytest
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# Out-of-bounds pixel access
# ---------------------------------------------------------------------------

def test_getpixel_out_of_bounds_raises():
    im = Image.new("RGB", (10, 10))
    with pytest.raises((IndexError, ValueError)):
        im.getpixel((10, 0))


def test_getpixel_negative_out_of_bounds_raises():
    """Negative index beyond wrap range raises IndexError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((IndexError, ValueError)):
        im.getpixel((-11, 0))


def test_getpixel_negative_wraps():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((9, 9), 200)
    assert im.getpixel((-1, -1)) == 200


def test_putpixel_out_of_bounds_raises():
    im = Image.new("RGB", (5, 5))
    with pytest.raises(Exception):
        im.putpixel((5, 0), (255, 0, 0))


# ---------------------------------------------------------------------------
# resize validation
# ---------------------------------------------------------------------------

def test_resize_zero_width_raises():
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.resize((0, 5))


def test_resize_zero_height_raises():
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.resize((5, 0))


def test_resize_negative_raises():
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.resize((-1, 5))


# ---------------------------------------------------------------------------
# crop validation
# ---------------------------------------------------------------------------

def test_crop_inverted_horizontal_raises():
    """right < left raises ValueError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.crop((8, 0, 2, 5))


def test_crop_inverted_vertical_raises():
    """lower < upper raises ValueError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.crop((0, 8, 5, 2))


def test_crop_out_of_bounds_ok():
    """Upstream: crop with out-of-bounds coords is allowed (zero-pads)."""
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = im.crop((-5, -5, 5, 5))
    assert out.size == (10, 10)
    # Corner at (-5,-5) should be black (padded)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    # Center at (5,5) offset = image origin
    assert out.getpixel((5, 5)) == (255, 0, 0)


def test_crop_zero_dimension():
    """right == left produces a zero-width image."""
    im = Image.new("RGB", (10, 10))
    out = im.crop((5, 0, 5, 10))
    assert out.size == (0, 10)


def test_crop_exact_bounds():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    out = im.crop((0, 0, 10, 10))
    assert out.size == (10, 10)
    assert out.getpixel((0, 0)) == (1, 2, 3)


# ---------------------------------------------------------------------------
# mode validation
# ---------------------------------------------------------------------------

def test_new_invalid_mode_raises():
    with pytest.raises(Exception):
        Image.new("XYZ", (10, 10))


def test_merge_wrong_mode_raises():
    """merge() with non-matching band count should raise."""
    im = Image.new("L", (5, 5))
    with pytest.raises(Exception):
        Image.merge("RGB", [im])  # need 3 bands


def test_convert_invalid_mode_raises():
    im = Image.new("RGB", (5, 5))
    with pytest.raises(Exception):
        im.convert("XYZ")


# ---------------------------------------------------------------------------
# paste validation
# ---------------------------------------------------------------------------

def test_paste_wrong_mode_no_crash():
    """paste() of different-mode image should work via conversion or error."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    dst.paste(src, (2, 2))
    assert dst.getpixel((4, 4)) == (255, 0, 0)


def test_paste_out_of_bounds_right():
    """Paste extends past the right edge — clipped."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    dst.paste(src, (8, 0))  # extends to x=13
    # Visible part (x=8..9) should be red
    assert dst.getpixel((9, 0)) == (255, 0, 0)
    assert dst.getpixel((7, 0)) == (0, 0, 0)


def test_paste_out_of_bounds_below():
    """Paste extends past the bottom edge — clipped."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (0, 255, 0))
    dst.paste(src, (0, 8))  # extends to y=13
    assert dst.getpixel((0, 9)) == (0, 255, 0)
    assert dst.getpixel((0, 7)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# alpha_composite validation
# ---------------------------------------------------------------------------

def test_alpha_composite_wrong_mode_raises():
    dst = Image.new("RGB", (5, 5))
    src = Image.new("RGBA", (5, 5))
    with pytest.raises(ValueError):
        Image.alpha_composite(dst, src)


def test_alpha_composite_both_wrong_mode_raises():
    dst = Image.new("RGB", (5, 5))
    src = Image.new("RGB", (5, 5))
    with pytest.raises(ValueError):
        Image.alpha_composite(dst, src)


def test_alpha_composite_instance_negative_dest_no_overlap():
    """Instance method: dest offset where src has no overlap is silently ignored."""
    dst = Image.new("RGBA", (5, 5), (0, 0, 255, 255))
    src = Image.new("RGBA", (3, 3), (255, 0, 0, 255))
    # src at (-10, -10) has no overlap, dst should be unchanged
    dst.alpha_composite(src, dest=(-10, -10))
    # dst should be unchanged (all blue)
    assert dst.getpixel((2, 2)) == (0, 0, 255, 255)


# ---------------------------------------------------------------------------
# rotate validation
# ---------------------------------------------------------------------------

def test_rotate_preserves_mode_and_size():
    for mode in ("L", "RGB", "RGBA"):
        im = Image.new(mode, (20, 30))
        out = im.rotate(45)
        assert out.mode == mode


# ---------------------------------------------------------------------------
# filter edge cases
# ---------------------------------------------------------------------------

def test_filter_RGBA_mode():
    """GaussianBlur on RGBA should not crash."""
    from PIL import ImageFilter
    im = Image.new("RGBA", (20, 20), (100, 150, 200, 128))
    out = im.filter(ImageFilter.GaussianBlur(radius=2))
    assert out.mode == "RGBA"
    assert out.size == (20, 20)


def test_filter_L_mode():
    from PIL import ImageFilter
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "L"


# ---------------------------------------------------------------------------
# thumbnail edge cases
# ---------------------------------------------------------------------------

def test_thumbnail_already_smaller():
    im = Image.new("RGB", (50, 50))
    im.thumbnail((100, 100))
    assert im.size == (50, 50)  # no change


def test_thumbnail_landscape():
    im = Image.new("RGB", (200, 100))
    im.thumbnail((100, 100))
    assert im.size == (100, 50)  # width limited


def test_thumbnail_portrait():
    im = Image.new("RGB", (100, 200))
    im.thumbnail((100, 100))
    assert im.size == (50, 100)  # height limited


# ---------------------------------------------------------------------------
# close() behavior
# ---------------------------------------------------------------------------

def test_close_then_mode_raises():
    """After close(), operations should raise."""
    im = Image.new("RGB", (5, 5))
    im.close()
    with pytest.raises(Exception):
        im.getpixel((0, 0))


def test_close_idempotent():
    """close() multiple times should not crash."""
    im = Image.new("RGB", (5, 5))
    im.close()
    im.close()  # should not raise
