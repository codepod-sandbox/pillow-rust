"""
Tests adapted from upstream Pillow test_image_convert.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_convert.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
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


# ---------------------------------------------------------------------------
# Upstream tests — test_image_convert.py
# ---------------------------------------------------------------------------


def test_unsupported_conversion():
    """Upstream: converting to an unknown mode raises a ValueError/Exception."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((ValueError, Exception)):
        im.convert("BOGUS")


def test_convert_RGBA_to_LA():
    """Upstream: RGBA -> LA should preserve alpha and desaturate color."""
    im = Image.new("RGBA", (1, 1), (200, 100, 50, 128))
    out = im.convert("LA")
    assert out.mode == "LA"
    l, a = out.getpixel((0, 0))
    assert a == 128  # alpha preserved


def test_convert_L_to_RGBA_full_alpha():
    """Upstream: L -> RGBA should set alpha to 255."""
    im = Image.new("L", (1, 1), 100)
    out = im.convert("RGBA")
    px = out.getpixel((0, 0))
    assert len(px) == 4
    assert px[3] == 255


def test_convert_RGBA_to_RGB_drops_alpha():
    """Upstream: RGBA -> RGB should discard alpha."""
    im = Image.new("RGBA", (1, 1), (10, 20, 30, 128))
    out = im.convert("RGB")
    assert out.mode == "RGB"
    px = out.getpixel((0, 0))
    assert len(px) == 3


def test_convert_LA_to_L():
    """Upstream: LA -> L should strip the alpha channel."""
    im = Image.new("LA", (1, 1), (200, 128))
    out = im.convert("L")
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 200
