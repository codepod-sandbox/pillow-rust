"""Tests for newly added PIL features."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageDraw, ImageEnhance, ImageOps


# ---------------------------------------------------------------------------
# paste
# ---------------------------------------------------------------------------

def test_paste_basic():
    bg = Image.new("RGB", (100, 100), (0, 0, 0))
    fg = Image.new("RGB", (20, 20), (255, 0, 0))
    bg.paste(fg, (10, 10))
    assert bg.getpixel((15, 15)) == (255, 0, 0)
    assert bg.getpixel((0, 0)) == (0, 0, 0)

def test_paste_no_box():
    bg = Image.new("RGB", (50, 50), (0, 0, 0))
    fg = Image.new("RGB", (50, 50), (0, 255, 0))
    bg.paste(fg)
    assert bg.getpixel((25, 25)) == (0, 255, 0)

def test_paste_with_mask():
    bg = Image.new("RGB", (50, 50), (0, 0, 0))
    fg = Image.new("RGB", (50, 50), (255, 255, 255))
    mask = Image.new("L", (50, 50), 128)
    bg.paste(fg, (0, 0), mask)
    r, g, b = bg.getpixel((25, 25))
    # Should be roughly half-blended
    assert 100 < r < 200
    assert 100 < g < 200

def test_paste_offset():
    bg = Image.new("RGB", (100, 100), (0, 0, 0))
    fg = Image.new("RGB", (10, 10), (0, 0, 255))
    bg.paste(fg, (90, 90))
    assert bg.getpixel((95, 95)) == (0, 0, 255)
    # Partially outside
    assert bg.getpixel((99, 99)) == (0, 0, 255)

# ---------------------------------------------------------------------------
# split / merge
# ---------------------------------------------------------------------------

def test_split_rgb():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    r, g, b = im.split()
    assert r.mode == "L"
    assert r.getpixel((5, 5)) == 100
    assert g.getpixel((5, 5)) == 150
    assert b.getpixel((5, 5)) == 200

def test_split_l():
    im = Image.new("L", (10, 10), 42)
    bands = im.split()
    assert len(bands) == 1
    assert bands[0].getpixel((5, 5)) == 42

def test_merge_rgb():
    r = Image.new("L", (10, 10), 10)
    g = Image.new("L", (10, 10), 20)
    b = Image.new("L", (10, 10), 30)
    im = Image.merge("RGB", [r, g, b])
    assert im.mode == "RGB"
    assert im.getpixel((5, 5)) == (10, 20, 30)

def test_split_merge_roundtrip():
    im = Image.new("RGB", (20, 20), (50, 100, 150))
    bands = im.split()
    merged = Image.merge("RGB", bands)
    assert merged.getpixel((10, 10)) == (50, 100, 150)

# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------

def test_histogram_L():
    im = Image.new("L", (10, 10), 42)
    hist = im.histogram()
    assert len(hist) == 256
    assert hist[42] == 100
    assert sum(hist) == 100

def test_histogram_RGB():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    hist = im.histogram()
    assert len(hist) == 768  # 256 * 3
    assert hist[10] == 25     # R channel
    assert hist[256 + 20] == 25  # G channel
    assert hist[512 + 30] == 25  # B channel

# ---------------------------------------------------------------------------
# getbbox / getextrema
# ---------------------------------------------------------------------------

def test_getbbox_nonzero():
    im = Image.new("RGB", (50, 50), (0, 0, 0))
    im.putpixel((10, 20), (255, 0, 0))
    im.putpixel((30, 40), (0, 255, 0))
    bbox = im.getbbox()
    assert bbox == (10, 20, 31, 41)

def test_getbbox_all_zero():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    assert im.getbbox() is None

def test_getextrema_L():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 1), 200)
    assert im.getextrema() == (50, 200)

def test_getextrema_RGB():
    im = Image.new("RGB", (10, 10), (100, 50, 200))
    result = im.getextrema()
    assert result == ((100, 100), (50, 50), (200, 200))

# ---------------------------------------------------------------------------
# thumbnail
# ---------------------------------------------------------------------------

def test_thumbnail_preserves_aspect():
    im = Image.new("RGB", (200, 100))
    im.thumbnail((100, 100))
    w, h = im.size
    assert w == 100
    assert h == 50

def test_thumbnail_already_fits():
    im = Image.new("RGB", (50, 50))
    im.thumbnail((100, 100))
    assert im.size == (50, 50)

# ---------------------------------------------------------------------------
# frombytes
# ---------------------------------------------------------------------------

def test_frombytes_L():
    data = bytes([42] * 100)
    im = Image.frombytes("L", (10, 10), data)
    assert im.mode == "L"
    assert im.getpixel((5, 5)) == 42

def test_frombytes_RGB():
    data = bytes([10, 20, 30] * 25)
    im = Image.frombytes("RGB", (5, 5), data)
    assert im.getpixel((2, 2)) == (10, 20, 30)

def test_frombytes_tobytes_roundtrip():
    orig = Image.new("RGB", (10, 10), (50, 100, 150))
    data = orig.tobytes()
    restored = Image.frombytes("RGB", (10, 10), data)
    assert restored.getpixel((5, 5)) == (50, 100, 150)

# ---------------------------------------------------------------------------
# ImageDraw: polygon, arc, pieslice
# ---------------------------------------------------------------------------

def test_polygon_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(10, 10), (90, 10), (50, 90)], fill=(255, 0, 0))
    assert im.getpixel((50, 30)) == (255, 0, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_polygon_outline():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(10, 50), (90, 50), (50, 10)], outline=(0, 255, 0))
    # Vertex should be drawn
    assert im.getpixel((10, 50)) == (0, 255, 0)

def test_arc_basic():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.arc([(10, 10), (90, 90)], 0, 180, fill=(255, 0, 0))
    # Right side of arc at 0 degrees
    assert im.getpixel((90, 50)) == (255, 0, 0)

def test_pieslice_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.pieslice([(10, 10), (90, 90)], 0, 90, fill=(0, 0, 255))
    # Center area of pie should be filled
    assert im.getpixel((55, 50)) == (0, 0, 255)

# ---------------------------------------------------------------------------
# ImageEnhance
# ---------------------------------------------------------------------------

def test_brightness_zero():
    im = Image.new("RGB", (10, 10), (100, 200, 50))
    out = ImageEnhance.Brightness(im).enhance(0.0)
    assert out.getpixel((5, 5)) == (0, 0, 0)

def test_brightness_one():
    im = Image.new("RGB", (10, 10), (100, 200, 50))
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (100, 200, 50)

def test_brightness_double():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    assert out.getpixel((5, 5)) == (200, 200, 200)

def test_contrast_zero():
    im = Image.new("RGB", (10, 10), (100, 200, 50))
    out = ImageEnhance.Contrast(im).enhance(0.0)
    r, g, b = out.getpixel((5, 5))
    # All channels should be the same (mean luminance)
    assert r == g == b

def test_color_zero():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageEnhance.Color(im).enhance(0.0)
    r, g, b = out.getpixel((5, 5))
    # Should be grey
    assert r == g == b

def test_sharpness_one():
    im = Image.new("RGB", (20, 20), (100, 100, 100))
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert out.getpixel((10, 10)) == (100, 100, 100)

# ---------------------------------------------------------------------------
# ImageOps
# ---------------------------------------------------------------------------

def test_grayscale():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    out = ImageOps.grayscale(im)
    assert out.mode == "L"

def test_flip():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((5, 0), (255, 0, 0))
    out = ImageOps.flip(im)
    assert out.getpixel((5, 9)) == (255, 0, 0)

def test_mirror():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((0, 5), (0, 255, 0))
    out = ImageOps.mirror(im)
    assert out.getpixel((9, 5)) == (0, 255, 0)

def test_invert():
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = ImageOps.invert(im)
    assert out.getpixel((5, 5)) == (155, 105, 55)

def test_autocontrast():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 1), 200)
    out = ImageOps.autocontrast(im)
    # Min should map to 0, max to 255
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 1)) == 255

def test_pad():
    im = Image.new("RGB", (100, 50), (255, 0, 0))
    out = ImageOps.pad(im, (100, 100), color=0)
    assert out.size == (100, 100)
    # Center should be red
    assert out.getpixel((50, 50)) == (255, 0, 0)

def test_contain():
    im = Image.new("RGB", (200, 100))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (100, 50)

def test_scale():
    im = Image.new("RGB", (50, 50))
    out = ImageOps.scale(im, 2.0)
    assert out.size == (100, 100)

def test_cover():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.cover(im, (100, 100))
    assert out.size == (100, 100)


if __name__ == "__main__":
    pytest.main()
