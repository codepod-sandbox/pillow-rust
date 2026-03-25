"""
Tests adapted from upstream Pillow test_image_paste.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_paste.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# paste another image
# ---------------------------------------------------------------------------


def test_paste_image_at_origin():
    dest = Image.new("RGB", (100, 100), (0, 0, 0))
    src = Image.new("RGB", (50, 50), (255, 0, 0))
    dest.paste(src)
    assert dest.getpixel((0, 0)) == (255, 0, 0)
    assert dest.getpixel((49, 49)) == (255, 0, 0)
    assert dest.getpixel((50, 50)) == (0, 0, 0)


def test_paste_image_at_offset():
    dest = Image.new("RGB", (100, 100), (0, 0, 0))
    src = Image.new("RGB", (20, 20), (0, 255, 0))
    dest.paste(src, (10, 10))
    assert dest.getpixel((0, 0)) == (0, 0, 0)
    assert dest.getpixel((10, 10)) == (0, 255, 0)
    assert dest.getpixel((29, 29)) == (0, 255, 0)
    assert dest.getpixel((30, 30)) == (0, 0, 0)


def test_paste_color_fill():
    dest = Image.new("RGB", (100, 100), (0, 0, 0))
    dest.paste((255, 128, 64), (10, 10, 50, 50))
    assert dest.getpixel((0, 0)) == (0, 0, 0)
    assert dest.getpixel((25, 25)) == (255, 128, 64)


def test_paste_color_int():
    dest = Image.new("RGB", (10, 10), (0, 0, 0))
    dest.paste(0, (0, 0, 10, 10))
    assert dest.getpixel((5, 5)) == (0, 0, 0)


def test_paste_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        dest = Image.new(mode, (50, 50))
        src = Image.new(mode, (20, 20))
        dest.paste(src, (5, 5))
        assert dest.mode == mode


def test_paste_larger_than_dest():
    """Pasting an image larger than the destination should clip."""
    dest = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (20, 20), (255, 255, 255))
    dest.paste(src, (0, 0))
    assert dest.getpixel((0, 0)) == (255, 255, 255)
    assert dest.getpixel((9, 9)) == (255, 255, 255)
    assert dest.size == (10, 10)  # dest size unchanged


# ---------------------------------------------------------------------------
# split / merge
# ---------------------------------------------------------------------------


def test_split_RGB():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    bands = im.split()
    assert len(bands) == 3
    for b in bands:
        assert b.mode == "L"
        assert b.size == (10, 10)
    assert bands[0].getpixel((0, 0)) == 10  # R
    assert bands[1].getpixel((0, 0)) == 20  # G
    assert bands[2].getpixel((0, 0)) == 30  # B


def test_split_RGBA():
    im = Image.new("RGBA", (10, 10), (10, 20, 30, 40))
    bands = im.split()
    assert len(bands) == 4
    assert bands[0].getpixel((0, 0)) == 10
    assert bands[1].getpixel((0, 0)) == 20
    assert bands[2].getpixel((0, 0)) == 30
    assert bands[3].getpixel((0, 0)) == 40


def test_split_L():
    im = Image.new("L", (10, 10), 42)
    bands = im.split()
    assert len(bands) == 1
    assert bands[0].getpixel((0, 0)) == 42


def test_merge_RGB():
    r = Image.new("L", (10, 10), 10)
    g = Image.new("L", (10, 10), 20)
    b = Image.new("L", (10, 10), 30)
    im = Image.merge("RGB", [r, g, b])
    assert im.mode == "RGB"
    assert im.getpixel((0, 0)) == (10, 20, 30)


def test_merge_RGBA():
    r = Image.new("L", (10, 10), 10)
    g = Image.new("L", (10, 10), 20)
    b = Image.new("L", (10, 10), 30)
    a = Image.new("L", (10, 10), 40)
    im = Image.merge("RGBA", [r, g, b, a])
    assert im.mode == "RGBA"
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)


def test_split_merge_roundtrip():
    im = Image.new("RGB", (10, 10), (42, 84, 126))
    bands = im.split()
    merged = Image.merge("RGB", list(bands))
    assert_image_equal(im, merged)


def test_split_merge_roundtrip_RGBA():
    im = Image.new("RGBA", (10, 10), (10, 20, 30, 40))
    bands = im.split()
    merged = Image.merge("RGBA", list(bands))
    assert_image_equal(im, merged)


# ---------------------------------------------------------------------------
# histogram / getcolors / getextrema
# ---------------------------------------------------------------------------


def test_histogram_L():
    im = Image.new("L", (10, 10), 42)
    hist = im.histogram()
    assert len(hist) == 256
    assert hist[42] == 100
    assert sum(hist) == 100


def test_histogram_RGB():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    hist = im.histogram()
    assert len(hist) == 768  # 256 * 3
    assert hist[10] == 100      # R channel
    assert hist[256 + 20] == 100  # G channel
    assert hist[512 + 30] == 100  # B channel


def test_getcolors_single():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    colors = im.getcolors()
    assert colors == [(100, (1, 2, 3))]


def test_getcolors_two():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    im.putpixel((0, 0), (4, 5, 6))
    colors = im.getcolors()
    assert len(colors) == 2
    count_map = {c: n for n, c in colors}
    assert count_map[(1, 2, 3)] == 99
    assert count_map[(4, 5, 6)] == 1


def test_getcolors_maxcolors():
    im = Image.new("L", (256, 1))
    for x in range(256):
        im.putpixel((x, 0), x)
    assert im.getcolors(maxcolors=256) is not None
    assert im.getcolors(maxcolors=255) is None


def test_getextrema_L():
    im = Image.new("L", (10, 10), 42)
    im.putpixel((0, 0), 10)
    im.putpixel((1, 0), 200)
    assert im.getextrema() == (10, 200)


def test_getextrema_RGB():
    im = Image.new("RGB", (10, 10), (50, 100, 150))
    im.putpixel((0, 0), (10, 20, 30))
    im.putpixel((1, 0), (200, 210, 220))
    extrema = im.getextrema()
    assert extrema[0] == (10, 200)
    assert extrema[1] == (20, 210)
    assert extrema[2] == (30, 220)


# ---------------------------------------------------------------------------
# putalpha
# ---------------------------------------------------------------------------


def test_putalpha_int():
    im = Image.new("RGB", (3, 3), (255, 0, 0))
    im.putalpha(128)
    assert im.mode == "RGBA"
    assert im.getpixel((0, 0)) == (255, 0, 0, 128)


def test_putalpha_image():
    im = Image.new("RGB", (3, 3), (255, 0, 0))
    alpha = Image.new("L", (3, 3), 64)
    im.putalpha(alpha)
    assert im.mode == "RGBA"
    assert im.getpixel((0, 0)) == (255, 0, 0, 64)


# ---------------------------------------------------------------------------
# point (LUT)
# ---------------------------------------------------------------------------


def test_point_function_L():
    im = Image.new("L", (10, 10), 100)
    out = im.point(lambda x: x * 2)
    assert out.getpixel((0, 0)) == 200


def test_point_function_invert():
    im = Image.new("L", (10, 10), 100)
    out = im.point(lambda x: 255 - x)
    assert out.getpixel((0, 0)) == 155


# ---------------------------------------------------------------------------
# Upstream tests — test_image_paste.py
# ---------------------------------------------------------------------------


def test_paste_image_same_mode():
    """Upstream: pasting an image of the same mode."""
    dst = Image.new("RGB", (20, 20), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    dst.paste(src, (3, 3))
    assert dst.getpixel((3, 3)) == (255, 0, 0)
    assert dst.getpixel((0, 0)) == (0, 0, 0)


def test_paste_with_mask():
    """Upstream: paste with an L mask blends based on alpha."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (5, 5), (200, 200, 200))
    mask = Image.new("L", (5, 5), 255)  # fully opaque
    dst.paste(src, (0, 0), mask)
    assert dst.getpixel((2, 2)) == (200, 200, 200)


def test_paste_zero_mask():
    """Upstream: paste with a zero (transparent) mask leaves destination unchanged."""
    dst = Image.new("RGB", (10, 10), (0, 0, 255))
    src = Image.new("RGB", (5, 5), (255, 0, 0))
    mask = Image.new("L", (5, 5), 0)  # fully transparent
    dst.paste(src, (0, 0), mask)
    assert dst.getpixel((2, 2)) == (0, 0, 255)


def test_paste_at_origin():
    """Upstream: pasting at (0,0) works correctly."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGB", (3, 3), (100, 100, 100))
    dst.paste(src, (0, 0))
    assert dst.getpixel((0, 0)) == (100, 100, 100)
    assert dst.getpixel((2, 2)) == (100, 100, 100)
    assert dst.getpixel((3, 3)) == (0, 0, 0)


def test_paste_RGBA_mask():
    """Upstream: paste with an RGBA mask image uses alpha channel."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    dst.paste(src, (0, 0), src)
    assert dst.getpixel((2, 2)) == (255, 0, 0)


def test_paste_L_into_RGB():
    """Upstream: pasting an L image into RGB via mode conversion."""
    dst = Image.new("RGB", (10, 10), (0, 0, 0))
    src = Image.new("L", (5, 5), 200)
    src_rgb = src.convert("RGB")
    dst.paste(src_rgb, (0, 0))
    assert dst.getpixel((2, 2)) == (200, 200, 200)
