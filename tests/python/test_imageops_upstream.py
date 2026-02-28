"""Tests for PIL.ImageOps module."""

from PIL import Image, ImageOps


# --- autocontrast ---

def test_autocontrast_L():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 200)
    out = ImageOps.autocontrast(im)
    assert out.mode == "L"
    assert out.size == (10, 10)
    mn, mx = out.getextrema()
    assert mn == 0
    assert mx == 255


def test_autocontrast_RGB():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    im.putpixel((0, 0), (50, 60, 70))
    im.putpixel((1, 0), (200, 210, 220))
    out = ImageOps.autocontrast(im)
    assert out.mode == "RGB"


def test_autocontrast_flat():
    """All same value — should not crash, all pixels become 0."""
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.autocontrast(im)
    assert out.getpixel((0, 0)) == 0


# --- contain ---

def test_contain_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (100, 50)


def test_contain_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 100)


def test_contain_already_fits():
    im = Image.new("RGB", (50, 30))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 30)


# --- fit ---

def test_fit_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_portrait():
    im = Image.new("RGB", (100, 300), (0, 255, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_square():
    im = Image.new("RGB", (200, 200))
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)


# --- pad ---

def test_pad_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)
    # Padding should be black by default
    assert out.getpixel((0, 0)) == (0, 0, 0)
    # Center should have image content
    assert out.getpixel((100, 100)) == (255, 0, 0)


def test_pad_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)


def test_pad_with_color():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200), color=(0, 0, 255))
    assert out.size == (200, 200)
    # Corner should be fill color
    assert out.getpixel((0, 0)) == (0, 0, 255)


def test_pad_already_fits():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    out = ImageOps.pad(im, (100, 100))
    assert out.size == (100, 100)
    assert out.getpixel((0, 0)) == (255, 0, 0)


# --- expand ---

def test_expand_default_black():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=10)
    assert out.size == (70, 70)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((10, 10)) == (255, 0, 0)


def test_expand_with_fill():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=5, fill=(0, 0, 255))
    assert out.size == (60, 60)
    assert out.getpixel((0, 0)) == (0, 0, 255)
    assert out.getpixel((5, 5)) == (255, 0, 0)


def test_expand_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(10, 20))
    assert out.size == (70, 90)


def test_expand_four_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(5, 10, 15, 20))
    assert out.size == (70, 80)
    assert out.getpixel((5, 10)) == (255, 0, 0)


def test_expand_L_mode():
    im = Image.new("L", (50, 50), 128)
    out = ImageOps.expand(im, border=5, fill=0)
    assert out.size == (60, 60)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((5, 5)) == 128
