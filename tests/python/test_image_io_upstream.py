"""
Tests adapted from upstream Pillow — file format I/O tests.

Tests PNG, JPEG, BMP, GIF, TIFF, WebP save/open roundtrips.
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# PNG roundtrip
# ---------------------------------------------------------------------------


def test_png_roundtrip_RGB(hopper):
    im = hopper("RGB")
    im.save("/tmp/_pil_upstream_png.png")
    im2 = Image.open("/tmp/_pil_upstream_png.png")
    assert_image(im2, "RGB", im.size)
    assert im.getpixel((0, 0)) == im2.getpixel((0, 0))
    assert im.getpixel((64, 64)) == im2.getpixel((64, 64))


def test_png_roundtrip_RGBA():
    im = Image.new("RGBA", (20, 20), (10, 20, 30, 40))
    im.save("/tmp/_pil_upstream_rgba.png")
    im2 = Image.open("/tmp/_pil_upstream_rgba.png")
    assert_image(im2, "RGBA", (20, 20))
    assert im2.getpixel((0, 0)) == (10, 20, 30, 40)


def test_png_roundtrip_L():
    im = Image.new("L", (20, 20), 128)
    im.save("/tmp/_pil_upstream_l.png")
    im2 = Image.open("/tmp/_pil_upstream_l.png")
    assert im2.mode == "L"
    assert im2.getpixel((0, 0)) == 128


# ---------------------------------------------------------------------------
# JPEG roundtrip (lossy — only check mode/size)
# ---------------------------------------------------------------------------


def test_jpeg_roundtrip():
    im = Image.new("RGB", (20, 20), (128, 64, 32))
    im.save("/tmp/_pil_upstream_jpg.jpg", "jpeg")
    im2 = Image.open("/tmp/_pil_upstream_jpg.jpg")
    assert_image(im2, "RGB", (20, 20))


# ---------------------------------------------------------------------------
# BMP roundtrip (lossless)
# ---------------------------------------------------------------------------


def test_bmp_roundtrip():
    im = Image.new("RGB", (10, 10), (99, 88, 77))
    im.save("/tmp/_pil_upstream_bmp.bmp", "bmp")
    im2 = Image.open("/tmp/_pil_upstream_bmp.bmp")
    assert_image(im2, "RGB", (10, 10))
    assert im2.getpixel((0, 0)) == (99, 88, 77)


# ---------------------------------------------------------------------------
# GIF roundtrip
# ---------------------------------------------------------------------------


def test_gif_roundtrip():
    im = Image.new("RGB", (10, 10), (33, 66, 99))
    im.save("/tmp/_pil_upstream_gif.gif", "gif")
    im2 = Image.open("/tmp/_pil_upstream_gif.gif")
    assert im2.size == (10, 10)


# ---------------------------------------------------------------------------
# TIFF roundtrip
# ---------------------------------------------------------------------------


def test_tiff_roundtrip():
    im = Image.new("RGB", (10, 10), (11, 22, 33))
    im.save("/tmp/_pil_upstream_tiff.tiff", "tiff")
    im2 = Image.open("/tmp/_pil_upstream_tiff.tiff")
    assert im2.size == (10, 10)


# ---------------------------------------------------------------------------
# Multi-format save/reopen
# ---------------------------------------------------------------------------


def test_multiformat_save():
    im = Image.new("RGB", (10, 10), (33, 66, 99))
    for fmt in ("png", "bmp", "gif", "tiff"):
        path = "/tmp/_pil_upstream_fmt." + fmt
        im.save(path, fmt)
        im2 = Image.open(path)
        assert im2.size == (10, 10)


# ---------------------------------------------------------------------------
# Open from bytes
# ---------------------------------------------------------------------------


def test_open_from_bytes():
    import _pil_native
    im = Image.new("RGB", (5, 5), (42, 42, 42))
    data = _pil_native.image_save(im._handle, "png")
    im2 = Image.open(data)
    assert im2.size == (5, 5)
    assert im2.getpixel((0, 0)) == (42, 42, 42)


# ---------------------------------------------------------------------------
# Save format from extension
# ---------------------------------------------------------------------------


def test_save_format_from_extension():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    im.save("/tmp/_pil_upstream_ext.png")
    im2 = Image.open("/tmp/_pil_upstream_ext.png")
    assert im2.getpixel((0, 0)) == (1, 2, 3)


# ---------------------------------------------------------------------------
# Integration: chain operations then save/reopen
# ---------------------------------------------------------------------------


def test_chain_operations():
    im = Image.new("RGB", (200, 100), (50, 100, 150))
    im = im.resize((100, 50))
    im = im.crop((10, 10, 60, 40))
    im = im.rotate(90)
    im = im.convert("L")
    im.save("/tmp/_pil_upstream_chain.png")
    im2 = Image.open("/tmp/_pil_upstream_chain.png")
    assert im2.mode == "L"
    assert im2.size == (30, 50)
