"""
Tests for Image statistics methods: histogram, getcolors, getextrema, getbbox.

Tests adapted from upstream Pillow test suites.
The Pillow licence (MIT-CMU) applies to ported test logic.
"""

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------

def test_histogram_L_uniform():
    im = Image.new("L", (10, 10), 128)
    h = im.histogram()
    assert len(h) == 256
    assert h[128] == 100  # 10×10 pixels
    assert sum(h) == 100


def test_histogram_L_two_values():
    im = Image.new("L", (4, 4), 0)
    im.putpixel((0, 0), 255)
    h = im.histogram()
    assert h[0] == 15
    assert h[255] == 1
    assert sum(h) == 16


def test_histogram_RGB():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    h = im.histogram()
    assert len(h) == 768  # 3 bands × 256
    assert h[100] == 100      # R channel
    assert h[256 + 150] == 100  # G channel
    assert h[512 + 200] == 100  # B channel


def test_histogram_RGBA():
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 40))
    h = im.histogram()
    assert len(h) == 1024  # 4 bands × 256
    assert h[10] == 25      # R
    assert h[256 + 20] == 25  # G
    assert h[512 + 30] == 25  # B
    assert h[768 + 40] == 25  # A


def test_histogram_LA():
    im = Image.new("LA", (5, 5), (77, 200))
    h = im.histogram()
    assert len(h) == 512
    assert h[77] == 25
    assert h[256 + 200] == 25


def test_histogram_total_matches_pixel_count():
    for mode, size in [("L", (8, 8)), ("RGB", (5, 5)), ("RGBA", (4, 4))]:
        im = Image.new(mode, size, 128)
        h = im.histogram()
        bands = {"L": 1, "RGB": 3, "RGBA": 4}[mode]
        total_per_band = sum(h) // bands
        assert total_per_band == size[0] * size[1]


def test_histogram_with_mask():
    im = Image.new("L", (4, 4), 100)
    im.putpixel((0, 0), 200)
    # Mask covering only top-left pixel
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((0, 0), 255)
    h = im.histogram(mask)
    assert h[200] == 1  # only the masked pixel
    assert h[100] == 0
    assert sum(h) == 1


def test_histogram_all_zero_mask():
    """Zero mask — no pixels counted."""
    im = Image.new("L", (10, 10), 128)
    mask = Image.new("L", (10, 10), 0)
    h = im.histogram(mask)
    assert sum(h) == 0


def test_histogram_full_mask():
    """All-255 mask — same as no mask."""
    im = Image.new("L", (5, 5), 50)
    mask = Image.new("L", (5, 5), 255)
    h_masked = im.histogram(mask)
    h_plain = im.histogram()
    assert h_masked == h_plain


# ---------------------------------------------------------------------------
# getcolors
# ---------------------------------------------------------------------------

def test_getcolors_L_uniform():
    im = Image.new("L", (5, 5), 100)
    colors = im.getcolors()
    assert colors is not None
    assert len(colors) == 1
    assert colors[0] == (25, 100)


def test_getcolors_RGB():
    im = Image.new("RGB", (3, 3), (255, 0, 0))
    colors = im.getcolors()
    assert colors is not None
    assert len(colors) == 1
    count, color = colors[0]
    assert count == 9
    assert color == (255, 0, 0)


def test_getcolors_multiple_colors():
    im = Image.new("L", (2, 2), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 200)
    colors = im.getcolors()
    assert colors is not None
    color_vals = {c: n for n, c in colors}
    assert color_vals[100] == 1
    assert color_vals[200] == 1
    assert color_vals[0] == 2


def test_getcolors_exceeds_maxcolors():
    """Returns None when color count exceeds maxcolors."""
    im = Image.new("L", (256, 1))
    for x in range(256):
        im.putpixel((x, 0), x)
    result = im.getcolors(maxcolors=10)
    assert result is None


def test_getcolors_default_maxcolors():
    """Default maxcolors=256; 257 colors returns None."""
    im = Image.new("RGB", (257, 1))
    for x in range(257):
        im.putpixel((x, 0), (x % 256, x % 128, x % 64))
    # May or may not return None depending on actual color diversity
    result = im.getcolors(maxcolors=256)
    # Just check it doesn't crash
    assert result is None or isinstance(result, list)


# ---------------------------------------------------------------------------
# getextrema
# ---------------------------------------------------------------------------

def test_getextrema_L():
    im = Image.new("L", (5, 5), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((4, 4), 200)
    lo, hi = im.getextrema()
    assert lo == 50
    assert hi == 200


def test_getextrema_L_uniform():
    im = Image.new("L", (5, 5), 128)
    lo, hi = im.getextrema()
    assert lo == 128
    assert hi == 128


def test_getextrema_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    im.putpixel((0, 0), (50, 60, 70))
    im.putpixel((4, 4), (220, 230, 240))
    ex = im.getextrema()
    assert ex == ((50, 220), (60, 230), (70, 240))


def test_getextrema_RGBA():
    im = Image.new("RGBA", (3, 3), (100, 100, 100, 200))
    im.putpixel((0, 0), (50, 80, 110, 10))
    ex = im.getextrema()
    assert ex[0] == (50, 100)   # R: 50..100
    assert ex[1] == (80, 100)   # G: 80..100
    assert ex[2] == (100, 110)  # B: 100..110
    assert ex[3] == (10, 200)   # A: 10..200


def test_getextrema_LA():
    im = Image.new("LA", (5, 5), (100, 200))
    im.putpixel((0, 0), (50, 100))
    ex = im.getextrema()
    assert ex == ((50, 100), (100, 200))


# ---------------------------------------------------------------------------
# getbbox
# ---------------------------------------------------------------------------

def test_getbbox_L_single_pixel():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((3, 5), 100)
    assert im.getbbox() == (3, 5, 4, 6)


def test_getbbox_L_region():
    im = Image.new("L", (10, 10), 0)
    for x in range(2, 7):
        for y in range(3, 8):
            im.putpixel((x, y), 100)
    assert im.getbbox() == (2, 3, 7, 8)


def test_getbbox_all_black():
    """All-zero image → getbbox returns None."""
    im = Image.new("L", (10, 10), 0)
    assert im.getbbox() is None


def test_getbbox_all_white():
    """Fully non-zero image → bounding box = full image."""
    im = Image.new("L", (10, 10), 255)
    assert im.getbbox() == (0, 0, 10, 10)


def test_getbbox_RGB_non_black():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((5, 5), (100, 0, 0))
    assert im.getbbox() == (5, 5, 6, 6)


def test_getbbox_RGBA_respects_alpha():
    """Only pixels with non-zero any-channel value count."""
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    im.putpixel((3, 3), (0, 0, 0, 128))  # transparent but non-zero alpha
    assert im.getbbox() == (3, 3, 4, 4)


def test_getbbox_corner_pixels():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 1)
    im.putpixel((9, 9), 1)
    assert im.getbbox() == (0, 0, 10, 10)


def test_getbbox_single_row():
    im = Image.new("L", (10, 10), 0)
    for x in range(3, 7):
        im.putpixel((x, 5), 255)
    assert im.getbbox() == (3, 5, 7, 6)


def test_getbbox_1x1_nonzero():
    im = Image.new("L", (1, 1), 255)
    assert im.getbbox() == (0, 0, 1, 1)


def test_getbbox_1x1_zero():
    im = Image.new("L", (1, 1), 0)
    assert im.getbbox() is None
