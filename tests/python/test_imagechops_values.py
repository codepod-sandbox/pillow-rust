"""Tests for ImageChops operations verifying exact pixel values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageChops


# ---------------------------------------------------------------------------
# add with scale / offset parameters
# ---------------------------------------------------------------------------

def test_add_scale_2():
    """add(a, b, scale=2.0) divides the sum by 2."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 100)
    out = ImageChops.add(im1, im2, scale=2.0)
    # (100 + 100) / 2.0 = 100
    assert out.getpixel((2, 2)) == 100


def test_add_scale_with_clamp():
    """add(a, b, scale=0.5) multiplies by 2 (divides by 0.5)."""
    im1 = Image.new("L", (5, 5), 50)
    im2 = Image.new("L", (5, 5), 50)
    out = ImageChops.add(im1, im2, scale=0.5)
    # (50 + 50) / 0.5 = 200
    assert out.getpixel((2, 2)) == 200


def test_add_offset_positive():
    """add with positive offset shifts the result up."""
    im1 = Image.new("L", (5, 5), 50)
    im2 = Image.new("L", (5, 5), 50)
    out = ImageChops.add(im1, im2, scale=1.0, offset=28)
    # (50 + 50) / 1.0 + 28 = 128
    assert out.getpixel((2, 2)) == 128


def test_add_offset_negative():
    """add with negative offset shifts the result down (clamped to 0)."""
    im1 = Image.new("L", (5, 5), 20)
    im2 = Image.new("L", (5, 5), 20)
    out = ImageChops.add(im1, im2, scale=1.0, offset=-50)
    # (20 + 20) - 50 = -10, clamped to 0
    assert out.getpixel((2, 2)) == 0


def test_add_both_scale_and_offset():
    """add(a, b, scale=2.0, offset=10): (a+b)/scale + offset."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 100)
    out = ImageChops.add(im1, im2, scale=2.0, offset=10)
    # (100 + 100) / 2.0 + 10 = 110
    assert out.getpixel((2, 2)) == 110


# ---------------------------------------------------------------------------
# subtract with scale / offset parameters
# ---------------------------------------------------------------------------

def test_subtract_scale_2():
    """subtract(a, b, scale=2.0): (a-b)/2.0."""
    im1 = Image.new("L", (5, 5), 200)
    im2 = Image.new("L", (5, 5), 100)
    out = ImageChops.subtract(im1, im2, scale=2.0)
    # (200 - 100) / 2.0 = 50
    assert out.getpixel((2, 2)) == 50


def test_subtract_offset_128():
    """subtract(a, b, offset=128) adds 128 to make differences visible."""
    im1 = Image.new("L", (5, 5), 200)
    im2 = Image.new("L", (5, 5), 100)
    out = ImageChops.subtract(im1, im2, scale=1.0, offset=128)
    # (200 - 100) / 1.0 + 128 = 228
    assert out.getpixel((2, 2)) == 228


def test_subtract_clamped_with_offset():
    """subtract with offset=128 for identical images gives 128."""
    im = Image.new("L", (5, 5), 150)
    out = ImageChops.subtract(im, im, scale=1.0, offset=128)
    # (150 - 150) + 128 = 128
    assert out.getpixel((2, 2)) == 128


def test_subtract_negative_result_offset():
    """subtract where result is negative before clamping."""
    im1 = Image.new("L", (5, 5), 50)
    im2 = Image.new("L", (5, 5), 200)
    out = ImageChops.subtract(im1, im2)
    # (50 - 200) = -150, clamped to 0
    assert out.getpixel((2, 2)) == 0


# ---------------------------------------------------------------------------
# subtract_modulo
# ---------------------------------------------------------------------------

def test_subtract_modulo_basic():
    """subtract_modulo wraps around."""
    im1 = Image.new("L", (5, 5), 50)
    im2 = Image.new("L", (5, 5), 200)
    out = ImageChops.subtract_modulo(im1, im2)
    # (50 - 200) % 256 = -150 % 256 = 106
    assert out.getpixel((2, 2)) == 106


def test_subtract_modulo_same():
    """subtract_modulo of same image is all zeros."""
    im = Image.new("L", (5, 5), 150)
    out = ImageChops.subtract_modulo(im, im)
    assert out.getpixel((2, 2)) == 0


def test_subtract_modulo_no_wrap():
    """subtract_modulo when a > b — no wrap needed."""
    im1 = Image.new("L", (5, 5), 200)
    im2 = Image.new("L", (5, 5), 50)
    out = ImageChops.subtract_modulo(im1, im2)
    # 200 - 50 = 150
    assert out.getpixel((2, 2)) == 150


# ---------------------------------------------------------------------------
# soft_light / hard_light / overlay — exact value checks
# ---------------------------------------------------------------------------

def test_hard_light_dark_src():
    """Hard light with b < 128: (2*a*b)/255."""
    # a = 100, b = 64 (< 128): 2*100*64/255 = 50 (truncated int division)
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 64)
    out = ImageChops.hard_light(im1, im2)
    expected = (2 * 100 * 64) // 255  # = 50
    assert out.getpixel((2, 2)) == expected


def test_hard_light_bright_src():
    """Hard light with b >= 128: 255 - (2*(255-a)*(255-b))/255."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = ImageChops.hard_light(im1, im2)
    expected = 255 - (2 * (255 - 100) * (255 - 200)) // 255
    assert out.getpixel((2, 2)) == expected


def test_overlay_is_hard_light_swapped():
    """overlay(a, b) == hard_light(b, a)."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    ov = ImageChops.overlay(im1, im2)
    hl = ImageChops.hard_light(im2, im1)
    assert ov.getpixel((2, 2)) == hl.getpixel((2, 2))


def test_soft_light_symmetry():
    """soft_light(a, a) should produce value close to a."""
    im = Image.new("L", (5, 5), 128)
    out = ImageChops.soft_light(im, im)
    # soft_light(128, 128) should be near 128
    result = out.getpixel((2, 2))
    assert abs(int(result) - 128) <= 5


# ---------------------------------------------------------------------------
# RGB mode operations with exact values
# ---------------------------------------------------------------------------

def test_add_rgb_with_scale():
    """RGB add with scale=2.0."""
    im1 = Image.new("RGB", (5, 5), (100, 120, 80))
    im2 = Image.new("RGB", (5, 5), (100, 120, 80))
    out = ImageChops.add(im1, im2, scale=2.0)
    # (100+100)/2=100, (120+120)/2=120, (80+80)/2=80
    assert out.getpixel((2, 2)) == (100, 120, 80)


def test_subtract_rgb_with_offset():
    """RGB subtract with offset=128."""
    im1 = Image.new("RGB", (5, 5), (200, 150, 100))
    im2 = Image.new("RGB", (5, 5), (100, 100, 100))
    out = ImageChops.subtract(im1, im2, scale=1.0, offset=128)
    # (200-100)+128=228, (150-100)+128=178, (100-100)+128=128
    assert out.getpixel((2, 2)) == (228, 178, 128)


def test_add_modulo_rgb():
    """RGB add_modulo wraps per channel."""
    im1 = Image.new("RGB", (5, 5), (200, 200, 200))
    im2 = Image.new("RGB", (5, 5), (100, 50, 10))
    out = ImageChops.add_modulo(im1, im2)
    r = (200 + 100) % 256  # 44
    g = (200 + 50) % 256   # 250
    b = (200 + 10) % 256   # 210
    assert out.getpixel((2, 2)) == (r, g, b)


# ---------------------------------------------------------------------------
# offset edge cases
# ---------------------------------------------------------------------------

def test_offset_single_axis():
    """offset(im, xoffset) without yoffset uses same value for both."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 200)
    out = ImageChops.offset(im, 3)
    assert out.getpixel((3, 3)) == 200


def test_offset_zero():
    """offset(im, 0, 0) should return an identical image."""
    im = Image.new("RGB", (10, 10), (50, 100, 150))
    im.putpixel((3, 5), (255, 0, 0))
    out = ImageChops.offset(im, 0, 0)
    assert out.getpixel((3, 5)) == (255, 0, 0)
    assert out.getpixel((0, 0)) == (50, 100, 150)


if __name__ == "__main__":
    pytest.main()
