"""Adapted from upstream Pillow Tests/test_image.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image
from helper import hopper, assert_image, assert_image_equal, SUPPORTED_MODES


@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_image_modes_success(mode):
    Image.new(mode, (1, 1))

def test_image_modes_fail():
    with pytest.raises(Exception):
        Image.new("BAD_MODE", (1, 1))

def test_width_height():
    im = Image.new("RGB", (1, 2))
    assert im.width == 1
    assert im.height == 2
    assert im.size == (1, 2)

# --- Image.new with color ---

def test_new_L_black():
    im = Image.new("L", (1, 1), 0)
    assert im.getpixel((0, 0)) == 0

def test_new_L_color():
    im = Image.new("L", (1, 1), 128)
    assert im.getpixel((0, 0)) == 128

def test_new_RGB_black():
    im = Image.new("RGB", (1, 1), 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_new_RGB_color():
    im = Image.new("RGB", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)

def test_new_RGBA_color():
    im = Image.new("RGBA", (1, 1), (10, 20, 30, 40))
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)

def test_new_LA_color():
    im = Image.new("LA", (1, 1), (100, 200))
    assert im.getpixel((0, 0)) == (100, 200)

# --- Size ---

@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_size(mode):
    im = Image.new(mode, (128, 128))
    assert im.size == (128, 128)

def test_size_various():
    im = Image.new("RGB", (33, 44))
    assert im.size == (33, 44)
    assert im.width == 33
    assert im.height == 44

# --- tobytes ---

def test_tobytes_sanity():
    data = hopper("RGB").tobytes()
    assert isinstance(data, bytes)
    assert len(data) > 0

def test_tobytes_L():
    im = Image.new("L", (3, 2), 42)
    data = im.tobytes()
    assert len(data) == 6

def test_tobytes_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))
    data = im.tobytes()
    assert len(data) == 12

def test_tobytes_RGBA():
    im = Image.new("RGBA", (2, 2), (10, 20, 30, 40))
    data = im.tobytes()
    assert len(data) == 16

# --- Save / open roundtrips ---

def test_save_open_png_roundtrip():
    im = hopper("RGB")
    im.save("/tmp/_test.png")
    im2 = Image.open("/tmp/_test.png")
    assert_image(im2, "RGB", im.size)
    assert im.getpixel((0, 0)) == im2.getpixel((0, 0))
    assert im.getpixel((64, 64)) == im2.getpixel((64, 64))

def test_save_open_jpeg_roundtrip():
    im = Image.new("RGB", (20, 20), (128, 64, 32))
    im.save("/tmp/_test.jpg", "jpeg")
    im2 = Image.open("/tmp/_test.jpg")
    assert_image(im2, "RGB", (20, 20))

def test_save_open_bmp_roundtrip():
    im = Image.new("RGB", (10, 10), (99, 88, 77))
    im.save("/tmp/_test.bmp", "bmp")
    im2 = Image.open("/tmp/_test.bmp")
    assert_image(im2, "RGB", (10, 10))
    assert im2.getpixel((0, 0)) == (99, 88, 77)

def test_save_format_from_extension():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    im.save("/tmp/_test_ext.png")
    im2 = Image.open("/tmp/_test_ext.png")
    assert im2.getpixel((0, 0)) == (1, 2, 3)

@pytest.mark.parametrize("fmt", ["png", "bmp", "gif", "tiff"])
def test_multiformat_save(fmt):
    im = Image.new("RGB", (10, 10), (33, 66, 99))
    path = f"/tmp/_test_fmt.{fmt}"
    im.save(path, fmt)
    im2 = Image.open(path)
    assert_image(im2, im2.mode, (10, 10))

# --- Close / context manager ---

def test_close():
    im = Image.new("RGB", (10, 10))
    im.close()
    assert im._handle is None

def test_context_manager():
    with Image.new("RGB", (10, 10)) as im:
        assert im.size == (10, 10)

# --- repr ---

def test_repr():
    im = Image.new("RGB", (10, 20))
    r = repr(im)
    assert "RGB" in r
    assert "10x20" in r

def test_repr_closed():
    im = Image.new("RGB", (10, 10))
    im.close()
    assert "closed" in repr(im)

# --- Copy ---

@pytest.mark.parametrize("mode", SUPPORTED_MODES)
def test_copy(mode):
    im = hopper(mode)
    out = im.copy()
    assert_image(out, mode, im.size)
    assert_image_equal(im, out)

def test_copy_independence():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    out = im.copy()
    out.putpixel((0, 0), (99, 99, 99))
    assert im.getpixel((0, 0)) == (1, 2, 3)
    assert out.getpixel((0, 0)) == (99, 99, 99)

# --- Convert ---

@pytest.mark.parametrize("src,dst", [
    ("RGB", "L"), ("RGB", "RGBA"), ("RGB", "LA"),
    ("L", "RGB"), ("L", "RGBA"),
    ("RGBA", "RGB"), ("RGBA", "L"),
])
def test_convert(src, dst):
    im = hopper(src)
    out = im.convert(dst)
    assert_image(out, dst, im.size)

def test_convert_noop():
    for mode in SUPPORTED_MODES:
        im = hopper(mode)
        out = im.convert(mode)
        assert_image(out, mode, im.size)

def test_convert_unsupported():
    with pytest.raises(Exception):
        hopper("RGB").convert("BOGUS")

def test_convert_white_to_L():
    im = Image.new("RGB", (1, 1), (255, 255, 255))
    assert im.convert("L").getpixel((0, 0)) == 255

def test_convert_black_to_L():
    im = Image.new("RGB", (1, 1), (0, 0, 0))
    assert im.convert("L").getpixel((0, 0)) == 0

def test_convert_rgb_to_rgba_alpha():
    im = Image.new("RGB", (1, 1), (100, 150, 200))
    out = im.convert("RGBA")
    r, g, b, a = out.getpixel((0, 0))
    assert a == 255
    assert (r, g, b) == (100, 150, 200)

# --- Pixel access ---

def test_getpixel_putpixel_L():
    im = Image.new("L", (1, 1))
    im.putpixel((0, 0), 128)
    assert im.getpixel((0, 0)) == 128

def test_getpixel_putpixel_RGB():
    im = Image.new("RGB", (1, 1))
    im.putpixel((0, 0), (10, 20, 30))
    assert im.getpixel((0, 0)) == (10, 20, 30)

def test_getpixel_putpixel_RGBA():
    im = Image.new("RGBA", (1, 1))
    im.putpixel((0, 0), (10, 20, 30, 40))
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)

def test_putpixel_overwrites():
    im = Image.new("RGB", (2, 2), (0, 0, 0))
    im.putpixel((1, 1), (255, 128, 64))
    assert im.getpixel((1, 1)) == (255, 128, 64)
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_getpixel_default():
    im = Image.new("RGB", (10, 10))
    assert im.getpixel((5, 5)) == (0, 0, 0)

def test_putpixel_scan():
    im = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), (x * 16, y * 16, (x + y) * 8))
    for y in range(16):
        for x in range(16):
            expected = (x * 16, y * 16, (x + y) * 8)
            assert im.getpixel((x, y)) == expected


if __name__ == "__main__":
    pytest.main()
