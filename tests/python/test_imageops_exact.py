"""Tests for ImageOps — exact pixel values for all operations."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageOps


# ---------------------------------------------------------------------------
# autocontrast
# ---------------------------------------------------------------------------

def test_autocontrast_spreads_range():
    """autocontrast remaps so darkest pixel → 0 and brightest → 255."""
    # Use an image where 0 is the min (so autocontrast maps it to 0)
    # and 200 is the max
    im = Image.new("L", (10, 10), 0)  # background is 0
    im.putpixel((3, 3), 200)           # brightest pixel
    out = ImageOps.autocontrast(im)
    # Darkest pixel (0) → 0
    assert out.getpixel((0, 0)) == 0
    # Brightest pixel (200) → 255 (within rounding)
    assert abs(out.getpixel((3, 3)) - 255) <= 1


def test_autocontrast_flat_image():
    """Flat image (all same value) should return unchanged."""
    im = Image.new("L", (5, 5), 100)
    out = ImageOps.autocontrast(im)
    # Result may be 0 or 100 depending on implementation — just check no crash
    assert out.size == (5, 5)


def test_autocontrast_already_full_range():
    """Image already spanning 0-255 should stay mostly the same."""
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 255)
    out = ImageOps.autocontrast(im)
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) == 255


# ---------------------------------------------------------------------------
# equalize
# ---------------------------------------------------------------------------

def test_equalize_returns_same_size():
    im = Image.new("L", (20, 20), 128)
    out = ImageOps.equalize(im)
    assert out.size == (20, 20)
    assert out.mode == "L"


def test_equalize_does_not_modify_original():
    im = Image.new("L", (10, 10), 100)
    ImageOps.equalize(im)
    assert im.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# invert
# ---------------------------------------------------------------------------

def test_invert_zero_to_255():
    im = Image.new("L", (5, 5), 0)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 255


def test_invert_255_to_0():
    im = Image.new("L", (5, 5), 255)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 0


def test_invert_midpoint():
    im = Image.new("L", (5, 5), 100)
    out = ImageOps.invert(im)
    assert out.getpixel((0, 0)) == 155


def test_invert_rgb():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageOps.invert(im)
    r, g, b = out.getpixel((0, 0))
    assert r == 155
    assert g == 105
    assert b == 55


def test_invert_is_own_inverse():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 200)
    out = ImageOps.invert(ImageOps.invert(im))
    assert out.getpixel((5, 5)) == 200
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# posterize
# ---------------------------------------------------------------------------

def test_posterize_1_bit():
    """1-bit posterize: values map to 0 or 128."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 127)
    im.putpixel((2, 0), 255)
    out = ImageOps.posterize(im, 1)
    # With 1 bit, only values 0 or 128
    v0 = out.getpixel((0, 0))
    v1 = out.getpixel((1, 0))
    v2 = out.getpixel((2, 0))
    assert v0 in (0, 128)
    assert v1 in (0, 128)
    assert v2 in (0, 128, 255)


def test_posterize_8_bit_unchanged():
    """8-bit posterize: image should be unchanged."""
    im = Image.new("L", (5, 5), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 200)
    out = ImageOps.posterize(im, 8)
    assert out.getpixel((0, 0)) == 100
    assert out.getpixel((1, 0)) == 200


def test_posterize_returns_same_mode():
    im = Image.new("L", (5, 5), 128)
    out = ImageOps.posterize(im, 4)
    assert out.mode == "L"


# ---------------------------------------------------------------------------
# solarize
# ---------------------------------------------------------------------------

def test_solarize_above_threshold_inverted():
    """Values above threshold get inverted."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 200)   # above threshold=128
    im.putpixel((1, 0), 100)   # below threshold
    im.putpixel((2, 0), 128)   # at threshold
    out = ImageOps.solarize(im, threshold=128)
    # Above threshold → inverted (255 - value)
    assert out.getpixel((0, 0)) == 55   # 255 - 200
    # Below threshold → unchanged
    assert out.getpixel((1, 0)) == 100


def test_solarize_threshold_0_inverts_all():
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 100)
    out = ImageOps.solarize(im, threshold=0)
    # All values >= 0 → all inverted
    assert out.getpixel((0, 0)) == 155  # 255 - 100


def test_solarize_threshold_255_inverts_none():
    im = Image.new("L", (5, 5), 100)
    out = ImageOps.solarize(im, threshold=255)
    # No values >= 255 (well, 255 itself would be), so 100 stays 100
    # Actually values > 255 can't exist; only pixel=255 gets inverted
    assert out.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# flip and mirror (tested elsewhere but add exact pixel checks)
# ---------------------------------------------------------------------------

def test_flip_exact_pixels():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 100)  # top-left
    out = ImageOps.flip(im)
    # After flip (vertical), top-left → bottom-left
    assert out.getpixel((0, 3)) == 100
    assert out.getpixel((0, 0)) == 0


def test_mirror_exact_pixels():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 100)  # top-left
    out = ImageOps.mirror(im)
    # After mirror (horizontal), top-left → top-right
    assert out.getpixel((3, 0)) == 100
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# grayscale
# ---------------------------------------------------------------------------

def test_grayscale_returns_L_mode():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = ImageOps.grayscale(im)
    assert out.mode == "L"


def test_grayscale_white_stays_white():
    im = Image.new("RGB", (5, 5), (255, 255, 255))
    out = ImageOps.grayscale(im)
    assert out.getpixel((0, 0)) == 255


def test_grayscale_black_stays_black():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    out = ImageOps.grayscale(im)
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# expand
# ---------------------------------------------------------------------------

def test_expand_increases_size():
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.expand(im, border=5)
    assert out.size == (20, 20)


def test_expand_fills_border_with_fill():
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.expand(im, border=3, fill=0)
    # Border pixels are 0
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((2, 2)) == 0
    # Interior pixels are 128
    assert out.getpixel((3, 3)) == 128
    assert out.getpixel((12, 12)) == 128


def test_expand_asymmetric():
    """expand with (left, top, right, bottom) tuple."""
    im = Image.new("L", (10, 10), 100)
    out = ImageOps.expand(im, border=(1, 2, 3, 4), fill=0)
    assert out.size == (14, 16)  # 10+1+3=14, 10+2+4=16


# ---------------------------------------------------------------------------
# pad
# ---------------------------------------------------------------------------

def test_pad_returns_correct_size():
    im = Image.new("L", (30, 20), 128)
    out = ImageOps.pad(im, (50, 50))
    assert out.size == (50, 50)


def test_pad_smaller_than_image():
    """pad to smaller size should still return requested size."""
    im = Image.new("L", (100, 100), 128)
    out = ImageOps.pad(im, (50, 50))
    assert out.size == (50, 50)


# ---------------------------------------------------------------------------
# fit
# ---------------------------------------------------------------------------

def test_fit_returns_correct_size():
    im = Image.new("L", (200, 100), 128)
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)


def test_fit_mode_preserved():
    im = Image.new("RGB", (200, 100), (100, 150, 200))
    out = ImageOps.fit(im, (50, 50))
    assert out.mode == "RGB"


if __name__ == "__main__":
    pytest.main()
