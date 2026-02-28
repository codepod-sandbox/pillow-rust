"""Tests for save() quality and optimize parameters."""

from PIL import Image


def test_save_jpeg_default_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_default.jpg")
    im2 = Image.open("/tmp/_pil_quality_default.jpg")
    assert im2.size == (100, 100)


def test_save_jpeg_low_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_low.jpg", quality=10)
    im2 = Image.open("/tmp/_pil_quality_low.jpg")
    assert im2.size == (100, 100)


def test_save_jpeg_high_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_high.jpg", quality=95)
    im2 = Image.open("/tmp/_pil_quality_high.jpg")
    assert im2.size == (100, 100)


def test_save_quality_affects_file_size():
    im = Image.new("RGB", (200, 200))
    for y in range(200):
        for x in range(200):
            im.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))
    im.save("/tmp/_pil_q10.jpg", quality=10)
    im.save("/tmp/_pil_q95.jpg", quality=95)
    _open = __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
    with _open("/tmp/_pil_q10.jpg", "rb") as f:
        size_low = len(f.read())
    with _open("/tmp/_pil_q95.jpg", "rb") as f:
        size_high = len(f.read())
    assert size_low < size_high


def test_save_png_ignores_quality():
    """PNG doesn't use quality -- should save normally without error."""
    im = Image.new("RGB", (50, 50), (0, 255, 0))
    im.save("/tmp/_pil_quality_png.png", quality=50)
    im2 = Image.open("/tmp/_pil_quality_png.png")
    assert im2.getpixel((0, 0)) == (0, 255, 0)


def test_save_jpeg_roundtrip_color():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    im.save("/tmp/_pil_quality_rt.jpg", quality=100)
    im2 = Image.open("/tmp/_pil_quality_rt.jpg")
    r, g, b = im2.getpixel((5, 5))
    assert r > 200  # JPEG is lossy, but at q=100 close to original


def test_save_optimize_flag():
    """optimize=True should not error."""
    im = Image.new("RGB", (50, 50), (0, 0, 255))
    im.save("/tmp/_pil_optimize.jpg", optimize=True)
    im2 = Image.open("/tmp/_pil_optimize.jpg")
    assert im2.size == (50, 50)
