"""Tests for Image.point(), Image.eval(), Image.blend() — upstream-style."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# point() with list LUT
# ---------------------------------------------------------------------------

def test_point_identity_L():
    """Identity LUT returns same image."""
    im = Image.new("L", (5, 5), 100)
    lut = list(range(256))
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 100


def test_point_invert_L():
    """Invert LUT: 255 - i."""
    im = Image.new("L", (5, 5), 100)
    lut = [255 - i for i in range(256)]
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 155


def test_point_all_zeros():
    """All-zero LUT maps everything to 0."""
    im = Image.new("L", (5, 5), 200)
    lut = [0] * 256
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 0


def test_point_all_255():
    """All-255 LUT maps everything to 255."""
    im = Image.new("L", (5, 5), 50)
    lut = [255] * 256
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 255


def test_point_threshold_to_binary():
    """Threshold at 128: values < 128 → 0, values >= 128 → 255."""
    lut = [255 if i >= 128 else 0 for i in range(256)]
    im = Image.new("L", (5, 1), 0)
    for i, v in enumerate([0, 127, 128, 200, 255]):
        im.putpixel((i, 0), v)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) == 0
    assert out.getpixel((2, 0)) == 255
    assert out.getpixel((3, 0)) == 255
    assert out.getpixel((4, 0)) == 255


def test_point_RGB_with_256_lut():
    """256-entry LUT should be auto-replicated for all 3 channels."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    lut = [255 - i for i in range(256)]  # invert
    out = im.point(lut)
    r, g, b = out.getpixel((0, 0))
    assert r == 155  # 255 - 100
    assert g == 105  # 255 - 150
    assert b == 55   # 255 - 200


def test_point_RGB_with_768_lut():
    """768-entry LUT applies separately to each channel."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    # R channel: identity; G channel: zero; B channel: invert
    r_lut = list(range(256))
    g_lut = [0] * 256
    b_lut = [255 - i for i in range(256)]
    lut = r_lut + g_lut + b_lut
    out = im.point(lut)
    r, g, b = out.getpixel((0, 0))
    assert r == 100   # identity
    assert g == 0     # all zero
    assert b == 55    # 255 - 200


def test_point_preserves_mode_L():
    im = Image.new("L", (5, 5), 100)
    out = im.point(list(range(256)))
    assert out.mode == "L"


def test_point_preserves_mode_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = im.point(list(range(256)))
    assert out.mode == "RGB"


def test_point_preserves_size():
    im = Image.new("L", (30, 20), 100)
    out = im.point(list(range(256)))
    assert out.size == (30, 20)


# ---------------------------------------------------------------------------
# point() with callable
# ---------------------------------------------------------------------------

def test_point_callable_double():
    """Callable LUT: lambda x: x * 2 (clamped)."""
    im = Image.new("L", (5, 5), 50)
    out = im.point(lambda x: x * 2)
    # 50 * 2 = 100
    assert out.getpixel((0, 0)) == 100


def test_point_callable_clamp():
    """Callable values > 255 should be clamped via &0xFF."""
    im = Image.new("L", (5, 5), 200)
    out = im.point(lambda x: x * 2)
    # 200 * 2 = 400, 400 & 0xFF = 144
    assert out.getpixel((0, 0)) == 144


def test_point_callable_rgb():
    """Callable on RGB applies to all channels."""
    im = Image.new("RGB", (5, 5), (50, 100, 150))
    out = im.point(lambda x: x * 2)
    r, g, b = out.getpixel((0, 0))
    assert r == 100
    assert g == 200
    assert b == 44   # 150*2=300, 300&0xFF=44


def test_point_does_not_modify_in_place():
    """point() returns a new image; original is unchanged."""
    im = Image.new("L", (5, 5), 100)
    out = im.point([255 - i for i in range(256)])
    assert im.getpixel((0, 0)) == 100   # unchanged
    assert out.getpixel((0, 0)) == 155  # inverted


# ---------------------------------------------------------------------------
# Image.eval() — applies function to each pixel
# ---------------------------------------------------------------------------

def test_image_eval_invert():
    im = Image.new("L", (5, 5), 100)
    out = Image.eval(im, lambda x: 255 - x)
    assert out.getpixel((0, 0)) == 155


def test_image_eval_clamp():
    im = Image.new("L", (5, 5), 200)
    out = Image.eval(im, lambda x: x * 2)
    # 200 * 2 = 400 & 0xFF = 144
    assert out.getpixel((0, 0)) == 144


def test_image_eval_rgb():
    im = Image.new("RGB", (5, 5), (100, 100, 100))
    out = Image.eval(im, lambda x: 200)
    r, g, b = out.getpixel((0, 0))
    assert r == 200
    assert g == 200
    assert b == 200


# ---------------------------------------------------------------------------
# Image.blend()
# ---------------------------------------------------------------------------

def test_blend_zero_alpha():
    """alpha=0 returns copy of im1."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0.0)
    assert out.getpixel((0, 0)) == 100


def test_blend_one_alpha():
    """alpha=1 returns copy of im2."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=1.0)
    assert out.getpixel((0, 0)) == 200


def test_blend_half():
    """alpha=0.5 is midpoint."""
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0.5)
    val = out.getpixel((0, 0))
    assert 148 <= int(val) <= 151  # 150 ± rounding


def test_blend_rgb():
    im1 = Image.new("RGB", (5, 5), (0, 0, 0))
    im2 = Image.new("RGB", (5, 5), (200, 100, 50))
    out = Image.blend(im1, im2, alpha=0.5)
    r, g, b = out.getpixel((0, 0))
    assert 98 <= r <= 102
    assert 48 <= g <= 52
    assert 23 <= b <= 27


def test_blend_preserves_mode():
    im1 = Image.new("L", (5, 5), 100)
    im2 = Image.new("L", (5, 5), 200)
    out = Image.blend(im1, im2, alpha=0.5)
    assert out.mode == "L"


def test_blend_preserves_size():
    im1 = Image.new("RGB", (10, 20), 0)
    im2 = Image.new("RGB", (10, 20), 255)
    out = Image.blend(im1, im2, alpha=0.3)
    assert out.size == (10, 20)


if __name__ == "__main__":
    pytest.main()
