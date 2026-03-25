"""
Tests for LA (grayscale + alpha) mode support.

Tests adapted from upstream Pillow test suites.
The Pillow licence (MIT-CMU) applies to ported test logic.
"""

import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageOps


# ---------------------------------------------------------------------------
# Basic LA creation and access
# ---------------------------------------------------------------------------

def test_LA_new():
    im = Image.new("LA", (10, 10), (128, 200))
    assert im.mode == "LA"
    assert im.size == (10, 10)
    assert im.getpixel((0, 0)) == (128, 200)


def test_LA_new_scalar():
    """Scalar fill for LA creates opaque gray."""
    im = Image.new("LA", (5, 5), 100)
    assert im.mode == "LA"


def test_LA_new_zero_alpha():
    im = Image.new("LA", (5, 5), (255, 0))
    assert im.getpixel((0, 0)) == (255, 0)


def test_LA_putpixel_getpixel():
    im = Image.new("LA", (5, 5), (0, 0))
    im.putpixel((2, 3), (200, 128))
    assert im.getpixel((2, 3)) == (200, 128)


def test_LA_getbands():
    im = Image.new("LA", (5, 5))
    assert im.getbands() == ("L", "A")


def test_LA_size():
    im = Image.new("LA", (30, 40), (100, 200))
    assert im.width == 30
    assert im.height == 40


# ---------------------------------------------------------------------------
# Convert
# ---------------------------------------------------------------------------

def test_LA_to_L():
    im = Image.new("LA", (5, 5), (128, 200))
    out = im.convert("L")
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


def test_LA_to_RGBA():
    im = Image.new("LA", (5, 5), (100, 150))
    out = im.convert("RGBA")
    assert out.mode == "RGBA"
    px = out.getpixel((0, 0))
    assert px[0] == 100  # R
    assert px[1] == 100  # G (same as L)
    assert px[2] == 100  # B (same as L)
    assert px[3] == 150  # A preserved


def test_LA_to_RGB():
    im = Image.new("LA", (5, 5), (128, 255))
    out = im.convert("RGB")
    assert out.mode == "RGB"
    px = out.getpixel((0, 0))
    assert px == (128, 128, 128)


def test_L_to_LA():
    im = Image.new("L", (5, 5), 100)
    out = im.convert("LA")
    assert out.mode == "LA"
    px = out.getpixel((0, 0))
    assert px[0] == 100  # L preserved


def test_RGB_to_LA():
    im = Image.new("RGB", (5, 5), (100, 100, 100))
    out = im.convert("LA")
    assert out.mode == "LA"


def test_RGBA_to_LA():
    im = Image.new("RGBA", (5, 5), (128, 128, 128, 200))
    out = im.convert("LA")
    assert out.mode == "LA"
    px = out.getpixel((0, 0))
    assert px[0] == 128  # L
    assert px[1] == 200  # A preserved


# ---------------------------------------------------------------------------
# Split / merge / getchannel
# ---------------------------------------------------------------------------

def test_LA_split():
    im = Image.new("LA", (5, 5), (100, 200))
    bands = im.split()
    assert len(bands) == 2
    assert bands[0].mode == "L"
    assert bands[0].getpixel((0, 0)) == 100
    assert bands[1].mode == "L"
    assert bands[1].getpixel((0, 0)) == 200


def test_LA_getchannel_L():
    im = Image.new("LA", (5, 5), (77, 200))
    ch = im.getchannel("L")
    assert ch.mode == "L"
    assert ch.getpixel((0, 0)) == 77


def test_LA_getchannel_A():
    im = Image.new("LA", (5, 5), (77, 200))
    ch = im.getchannel("A")
    assert ch.mode == "L"
    assert ch.getpixel((0, 0)) == 200


def test_LA_merge():
    L = Image.new("L", (5, 5), 100)
    A = Image.new("L", (5, 5), 200)
    im = Image.merge("LA", [L, A])
    assert im.mode == "LA"
    assert im.getpixel((0, 0)) == (100, 200)


# ---------------------------------------------------------------------------
# Copy / crop / resize / paste
# ---------------------------------------------------------------------------

def test_LA_copy():
    im = Image.new("LA", (5, 5), (128, 100))
    cp = im.copy()
    assert cp.mode == "LA"
    assert cp.getpixel((0, 0)) == (128, 100)


def test_LA_crop():
    im = Image.new("LA", (10, 10), (50, 200))
    out = im.crop((2, 2, 8, 8))
    assert out.mode == "LA"
    assert out.size == (6, 6)
    assert out.getpixel((0, 0)) == (50, 200)


def test_LA_resize():
    im = Image.new("LA", (10, 10), (100, 200))
    out = im.resize((5, 5))
    assert out.mode == "LA"
    assert out.size == (5, 5)


def test_LA_rotate():
    im = Image.new("LA", (10, 10), (100, 200))
    out = im.rotate(90)
    assert out.mode == "LA"


def test_LA_transpose_flip():
    im = Image.new("LA", (4, 4), (100, 200))
    im.putpixel((0, 0), (50, 100))
    out = im.transpose(Image.FLIP_LEFT_RIGHT)
    assert out.mode == "LA"
    assert out.getpixel((3, 0)) == (50, 100)


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

def test_LA_filter_blur():
    im = Image.new("LA", (20, 20), (100, 200))
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "LA"
    assert out.size == (20, 20)


def test_LA_filter_sharpen():
    im = Image.new("LA", (20, 20), (100, 200))
    out = im.filter(ImageFilter.SHARPEN)
    assert out.mode == "LA"


def test_LA_filter_gaussian():
    im = Image.new("LA", (20, 20), (100, 200))
    out = im.filter(ImageFilter.GaussianBlur(radius=2))
    assert out.mode == "LA"


# ---------------------------------------------------------------------------
# Histogram / getextrema on LA
# ---------------------------------------------------------------------------

def test_LA_histogram():
    im = Image.new("LA", (5, 5), (100, 200))
    h = im.histogram()
    assert len(h) == 512  # 2 bands × 256
    # L channel: all pixels at 100
    assert h[100] == 25
    # A channel: all pixels at 200
    assert h[256 + 200] == 25


def test_LA_getextrema():
    im = Image.new("LA", (5, 5), (100, 200))
    im.putpixel((0, 0), (50, 100))
    ex = im.getextrema()
    assert ex == ((50, 100), (100, 200))


# ---------------------------------------------------------------------------
# Drawing on LA
# ---------------------------------------------------------------------------

def test_LA_draw_rectangle_tuple_fill():
    """Draw rectangle with (L, A) fill on LA image."""
    im = Image.new("LA", (20, 20), (0, 0))
    draw = ImageDraw.Draw(im)
    draw.rectangle([2, 2, 18, 18], fill=(128, 200))
    assert im.getpixel((10, 10)) == (128, 200)


def test_LA_draw_ellipse():
    im = Image.new("LA", (50, 50), (0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse([10, 10, 40, 40], fill=(200, 255))
    # Center should be painted
    assert im.getpixel((25, 25))[0] == 200


def test_LA_draw_line():
    im = Image.new("LA", (20, 20), (0, 0))
    draw = ImageDraw.Draw(im)
    draw.line([0, 0, 19, 0], fill=(150, 200))
    assert im.getpixel((10, 0)) == (150, 200)


def test_LA_draw_polygon():
    im = Image.new("LA", (50, 50), (0, 0))
    draw = ImageDraw.Draw(im)
    draw.polygon([10, 10, 40, 10, 25, 40], fill=(180, 255))
    # Interior should be filled
    assert im.getpixel((25, 20))[0] == 180


# ---------------------------------------------------------------------------
# tobytes / frombytes roundtrip
# ---------------------------------------------------------------------------

def test_LA_tobytes_frombytes():
    im = Image.new("LA", (5, 5), (77, 200))
    raw = im.tobytes()
    assert len(raw) == 5 * 5 * 2  # 2 bytes per pixel
    im2 = Image.frombytes("LA", (5, 5), raw)
    assert im2.getpixel((0, 0)) == (77, 200)


def test_LA_getdata_putdata():
    im = Image.new("LA", (3, 3), (50, 100))
    data = im.getdata()
    assert data[0] == (50, 100)
    im2 = Image.new("LA", (3, 3))
    im2.putdata(data)
    assert im2.getpixel((1, 1)) == (50, 100)


# ---------------------------------------------------------------------------
# point()
# ---------------------------------------------------------------------------

def test_LA_point_callable():
    im = Image.new("LA", (5, 5), (100, 200))
    out = im.point(lambda v: 255 - v)
    px = out.getpixel((0, 0))
    assert px[0] == 155   # 255 - 100
    assert px[1] == 55    # 255 - 200


def test_LA_point_lut():
    im = Image.new("LA", (5, 5), (50, 100))
    lut = list(range(256)) + [255 - i for i in range(256)]  # L passthrough, A inverted
    out = im.point(lut)
    px = out.getpixel((0, 0))
    assert px[0] == 50    # L unchanged
    assert px[1] == 155   # 255 - 100
