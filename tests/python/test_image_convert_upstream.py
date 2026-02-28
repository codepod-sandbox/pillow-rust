"""
Tests adapted from upstream Pillow test_image_convert.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_convert.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# Sanity: convert between all supported modes
# ---------------------------------------------------------------------------


def test_convert_sanity(hopper):
    modes = ("L", "LA", "RGB", "RGBA")
    for input_mode in modes:
        im = hopper(input_mode)
        for output_mode in modes:
            out = im.convert(output_mode)
            assert out.mode == output_mode
            assert out.size == im.size


# ---------------------------------------------------------------------------
# Specific conversions
# ---------------------------------------------------------------------------


def test_convert_RGB_to_L(hopper):
    im = hopper("RGB")
    out = im.convert("L")
    assert_image(out, "L", im.size)


def test_convert_RGB_to_RGBA(hopper):
    im = hopper("RGB")
    out = im.convert("RGBA")
    assert_image(out, "RGBA", im.size)


def test_convert_RGB_to_LA(hopper):
    im = hopper("RGB")
    out = im.convert("LA")
    assert_image(out, "LA", im.size)


def test_convert_L_to_RGB(hopper):
    im = hopper("L")
    out = im.convert("RGB")
    assert_image(out, "RGB", im.size)


def test_convert_L_to_RGBA(hopper):
    im = hopper("L")
    out = im.convert("RGBA")
    assert_image(out, "RGBA", im.size)


def test_convert_RGBA_to_RGB(hopper):
    im = hopper("RGBA")
    out = im.convert("RGB")
    assert_image(out, "RGB", im.size)


def test_convert_RGBA_to_L(hopper):
    im = hopper("RGBA")
    out = im.convert("L")
    assert_image(out, "L", im.size)


def test_convert_preserves_size(hopper):
    for src in ("L", "RGB", "RGBA"):
        for dst in ("L", "RGB", "RGBA"):
            im = hopper(src)
            out = im.convert(dst)
            assert out.size == im.size


def test_convert_noop(hopper):
    """Converting to the same mode should produce an equal image."""
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.convert(mode)
        assert_image(out, mode, im.size)


def test_convert_white_pixel():
    """White in RGB should map to 255 in L."""
    im = Image.new("RGB", (1, 1), (255, 255, 255))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 255


def test_convert_black_pixel():
    im = Image.new("RGB", (1, 1), (0, 0, 0))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 0


def test_convert_rgb_to_rgba_alpha():
    """RGB->RGBA should set alpha to 255."""
    im = Image.new("RGB", (1, 1), (100, 150, 200))
    out = im.convert("RGBA")
    r, g, b, a = out.getpixel((0, 0))
    assert a == 255
    assert (r, g, b) == (100, 150, 200)


def test_convert_L_to_LA():
    im = Image.new("L", (1, 1), 128)
    out = im.convert("LA")
    assert out.mode == "LA"
    l, a = out.getpixel((0, 0))
    assert l == 128
    assert a == 255  # full opacity


def test_convert_default():
    """convert() with no args should default to RGB."""
    im = Image.new("L", (10, 10), 128)
    out = im.convert()
    assert out.mode == "RGB"


def test_convert_roundtrip_RGB_L_RGB():
    """RGB -> L -> RGB roundtrip for pure white/black."""
    for color, expected_l in [((255, 255, 255), 255), ((0, 0, 0), 0)]:
        im = Image.new("RGB", (1, 1), color)
        l_im = im.convert("L")
        assert l_im.getpixel((0, 0)) == expected_l
        rgb_im = l_im.convert("RGB")
        px = rgb_im.getpixel((0, 0))
        assert px == (expected_l, expected_l, expected_l)
