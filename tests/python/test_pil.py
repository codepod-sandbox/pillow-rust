"""
Pillow compatibility tests for the codepod WASM implementation.

Adapted from the upstream Pillow test suite:
  https://github.com/python-pillow/Pillow/tree/main/Tests

Tests are grouped by the source Pillow file they derive from.
We cannot use pytest in the WASM sandbox, so we use a simple runner.
"""

from PIL import Image, ImageFilter, ImageDraw
import _pil_native

# ---------------------------------------------------------------------------
# Helpers  (adapted from Tests/helper.py)
# ---------------------------------------------------------------------------

_pass = 0
_fail = 0


def run(name, fn):
    global _pass, _fail
    try:
        fn()
        _pass += 1
        print(f"  PASS  {name}")
    except Exception as e:
        _fail += 1
        print(f"  FAIL  {name}: {e}")


def assert_image(im, mode, size):
    assert im.mode == mode, f"expected mode {mode}, got {im.mode}"
    assert im.size == size, f"expected size {size}, got {im.size}"


def assert_image_equal(a, b):
    assert a.mode == b.mode, f"mode mismatch: {a.mode} vs {b.mode}"
    assert a.size == b.size, f"size mismatch: {a.size} vs {b.size}"
    assert a.tobytes() == b.tobytes(), "pixel data differs"


def hopper(mode="RGB"):
    """Create a deterministic 128x128 test image (replaces Pillow's hopper())."""
    if mode in ("RGB", "RGBA", "L", "LA"):
        im = Image.new("RGB", (128, 128))
        for y in range(128):
            for x in range(128):
                r = (x * 2) % 256
                g = (y * 2) % 256
                b = ((x + y) * 3) % 256
                im.putpixel((x, y), (r, g, b))
        if mode != "RGB":
            im = im.convert(mode)
        return im
    return Image.new(mode, (128, 128))


# ===================================================================
# Tests/test_image.py — core Image tests
# ===================================================================
print("--- test_image ---")


def test_new_L():
    im = Image.new("L", (100, 100))
    assert_image(im, "L", (100, 100))

def test_new_RGB():
    im = Image.new("RGB", (100, 100))
    assert_image(im, "RGB", (100, 100))

def test_new_RGBA():
    im = Image.new("RGBA", (100, 100))
    assert_image(im, "RGBA", (100, 100))

def test_new_LA():
    im = Image.new("LA", (100, 100))
    assert_image(im, "LA", (100, 100))

def test_new_L_color():
    im = Image.new("L", (1, 1), 128)
    assert im.getpixel((0, 0)) == 128

def test_new_RGB_color():
    im = Image.new("RGB", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)

def test_new_RGBA_color():
    im = Image.new("RGBA", (1, 1), (10, 20, 30, 40))
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)

def test_new_L_black():
    im = Image.new("L", (1, 1), 0)
    assert im.getpixel((0, 0)) == 0

def test_new_RGB_black():
    im = Image.new("RGB", (1, 1), 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_width_height():
    im = Image.new("RGB", (1, 2))
    assert im.width == 1
    assert im.height == 2

def test_width_height_large():
    im = Image.new("RGB", (123, 456))
    assert im.width == 123
    assert im.height == 456

def test_size_property():
    im = Image.new("RGB", (33, 44))
    assert im.size == (33, 44)

def test_tobytes_sanity():
    data = hopper("RGB").tobytes()
    assert isinstance(data, bytes)
    assert len(data) > 0

def test_tobytes_L():
    im = Image.new("L", (3, 2), 42)
    data = im.tobytes()
    assert isinstance(data, bytes)
    # 3x2 L = 6 bytes
    assert len(data) == 6

def test_tobytes_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))
    data = im.tobytes()
    assert len(data) == 12  # 2*2*3

def test_tobytes_RGBA():
    im = Image.new("RGBA", (2, 2), (10, 20, 30, 40))
    data = im.tobytes()
    assert len(data) == 16  # 2*2*4

def test_save_open_png_roundtrip():
    """Adapted from test_image.py: test_string"""
    im = hopper("RGB")
    im.save("/tmp/_pil_test.png")
    im2 = Image.open("/tmp/_pil_test.png")
    assert_image(im2, "RGB", im.size)
    # pixel spot-check
    assert im.getpixel((0, 0)) == im2.getpixel((0, 0))
    assert im.getpixel((64, 64)) == im2.getpixel((64, 64))

def test_save_open_jpeg_roundtrip():
    im = Image.new("RGB", (20, 20), (128, 64, 32))
    im.save("/tmp/_pil_test.jpg", "jpeg")
    im2 = Image.open("/tmp/_pil_test.jpg")
    assert_image(im2, "RGB", (20, 20))
    # JPEG is lossy — just check the image loaded

def test_save_open_bmp_roundtrip():
    im = Image.new("RGB", (10, 10), (99, 88, 77))
    im.save("/tmp/_pil_test.bmp", "bmp")
    im2 = Image.open("/tmp/_pil_test.bmp")
    assert_image(im2, "RGB", (10, 10))
    # BMP is lossless
    assert im2.getpixel((0, 0)) == (99, 88, 77)

def test_save_format_from_extension():
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    im.save("/tmp/_pil_test_ext.png")
    im2 = Image.open("/tmp/_pil_test_ext.png")
    assert im2.getpixel((0, 0)) == (1, 2, 3)

def test_close():
    im = Image.new("RGB", (10, 10))
    im.close()
    # After close, handle should be None
    assert im._handle is None

def test_context_manager():
    with Image.new("RGB", (10, 10)) as im:
        assert im.size == (10, 10)

def test_repr():
    im = Image.new("RGB", (10, 20))
    r = repr(im)
    assert "RGB" in r
    assert "10x20" in r

def test_repr_closed():
    im = Image.new("RGB", (10, 10))
    im.close()
    r = repr(im)
    assert "closed" in r


for _n, _f in list(locals().items()):
    if _n.startswith("test_") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_resize.py — resize
# ===================================================================
print("\n--- test_image_resize ---")


def test_resize_RGB():
    out = hopper("RGB").resize((112, 103))
    assert_image(out, "RGB", (112, 103))

def test_resize_L():
    out = hopper("L").resize((112, 103))
    assert_image(out, "L", (112, 103))

def test_resize_RGBA():
    out = hopper("RGBA").resize((112, 103))
    assert_image(out, "RGBA", (112, 103))

def test_resize_enlarge():
    out = hopper("RGB").resize((212, 195))
    assert_image(out, "RGB", (212, 195))

def test_resize_down():
    out = hopper("RGB").resize((15, 12))
    assert_image(out, "RGB", (15, 12))

def test_resize_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        out = hopper(mode).resize((20, 20))
        assert out.mode == mode, f"mode changed from {mode} to {out.mode}"

def test_resize_1x1():
    out = hopper("RGB").resize((1, 1))
    assert_image(out, "RGB", (1, 1))


for _n, _f in list(locals().items()):
    if _n.startswith("test_resize") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_crop.py — crop
# ===================================================================
print("\n--- test_image_crop ---")


def test_crop_basic_RGB():
    im = hopper("RGB")
    cropped = im.crop((50, 50, 100, 100))
    assert_image(cropped, "RGB", (50, 50))

def test_crop_basic_L():
    im = hopper("L")
    cropped = im.crop((50, 50, 100, 100))
    assert_image(cropped, "L", (50, 50))

def test_crop_basic_RGBA():
    im = hopper("RGBA")
    cropped = im.crop((50, 50, 100, 100))
    assert_image(cropped, "RGBA", (50, 50))

def test_crop_preserves_mode():
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.crop((10, 10, 50, 50))
        assert out.mode == mode

def test_crop_preserves_pixels():
    im = Image.new("RGB", (100, 100), (42, 43, 44))
    cropped = im.crop((25, 25, 75, 75))
    assert cropped.getpixel((0, 0)) == (42, 43, 44)
    assert cropped.getpixel((24, 24)) == (42, 43, 44)

def test_crop_none():
    """crop() with no args should return a full copy."""
    im = hopper("RGB")
    cropped = im.crop()
    assert_image_equal(cropped, im)

def test_crop_full():
    im = Image.new("RGB", (100, 100), (1, 2, 3))
    cropped = im.crop((0, 0, 100, 100))
    assert_image(cropped, "RGB", (100, 100))
    assert cropped.getpixel((0, 0)) == (1, 2, 3)

def test_crop_single_pixel():
    im = Image.new("RGB", (10, 10), (5, 6, 7))
    im.putpixel((3, 4), (99, 98, 97))
    cropped = im.crop((3, 4, 4, 5))
    assert_image(cropped, "RGB", (1, 1))
    assert cropped.getpixel((0, 0)) == (99, 98, 97)


for _n, _f in list(locals().items()):
    if _n.startswith("test_crop") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_rotate.py — rotate
# ===================================================================
print("\n--- test_image_rotate ---")


def test_rotate_0():
    im = hopper("RGB")
    out = im.rotate(0)
    assert_image(out, "RGB", im.size)

def test_rotate_90_mode():
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.rotate(90)
        assert out.mode == mode

def test_rotate_90_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(90)
    assert out.size == (50, 100)

def test_rotate_180_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(180)
    assert out.size == (100, 50)

def test_rotate_270_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(270)
    assert out.size == (50, 100)

def test_rotate_360():
    im = hopper("RGB")
    out = im.rotate(360)
    assert_image(out, "RGB", im.size)

def test_rotate_90_pixel():
    """After 90° CCW rotation, (x,y) maps to (y, w-1-x)."""
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(90)
    # 10x20 → 20x10; pixel (0,0) should be at (0, 9) in rotated image
    assert out.size == (20, 10)
    assert out.getpixel((0, 9)) == (255, 0, 0)

def test_rotate_180_pixel():
    im = Image.new("RGB", (10, 10))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(180)
    assert out.getpixel((9, 9)) == (255, 0, 0)

def test_rotate_270_pixel():
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(270)
    assert out.size == (20, 10)
    assert out.getpixel((19, 0)) == (255, 0, 0)

def test_rotate_arbitrary():
    """Non-90° rotation should keep same dimensions, no crash."""
    im = Image.new("RGB", (100, 100), (0, 255, 0))
    out = im.rotate(45)
    assert_image(out, im.mode, im.size)


for _n, _f in list(locals().items()):
    if _n.startswith("test_rotate") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_transpose.py — transpose
# ===================================================================
print("\n--- test_image_transpose ---")


def _make_marker():
    """Create a non-square image with a unique pixel at (1,1)."""
    im = Image.new("RGB", (121, 127))
    im.putpixel((1, 1), (255, 0, 0))
    return im


def test_flip_left_right():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.FLIP_LEFT_RIGHT)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, 1))

def test_flip_top_bottom():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.FLIP_TOP_BOTTOM)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((1, y - 2))

def test_rotate_90_transpose():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_90)
    assert out.mode == im.mode
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, x - 2))

def test_rotate_180_transpose():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_180)
    assert out.mode == im.mode
    assert out.size == im.size
    assert im.getpixel((1, 1)) == out.getpixel((x - 2, y - 2))

def test_rotate_270_transpose():
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.ROTATE_270)
    assert out.mode == im.mode
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, 1))

def test_transpose_op():
    """TRANSPOSE = mirror along main diagonal."""
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.TRANSPOSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((1, 1))

def test_transverse_op():
    """TRANSVERSE = mirror along anti-diagonal."""
    im = _make_marker()
    x, y = im.size
    out = im.transpose(Image.TRANSVERSE)
    assert out.size == (y, x)
    assert im.getpixel((1, 1)) == out.getpixel((y - 2, x - 2))

def test_transpose_flip_lr_roundtrip():
    im = _make_marker()
    out = im.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_LEFT_RIGHT)
    assert_image_equal(im, out)

def test_transpose_flip_tb_roundtrip():
    im = _make_marker()
    out = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_TOP_BOTTOM)
    assert_image_equal(im, out)

def test_transpose_rotate_roundtrip():
    im = _make_marker()
    out = im.transpose(Image.ROTATE_90).transpose(Image.ROTATE_270)
    assert_image_equal(im, out)

def test_transpose_rotate_180_roundtrip():
    im = _make_marker()
    out = im.transpose(Image.ROTATE_180).transpose(Image.ROTATE_180)
    assert_image_equal(im, out)

def test_transpose_L():
    im = Image.new("L", (121, 127))
    im.putpixel((1, 1), 200)
    out = im.transpose(Image.FLIP_LEFT_RIGHT)
    assert out.mode == "L"
    assert out.getpixel((119, 1)) == 200


for _n, _f in list(locals().items()):
    if _n.startswith("test_transpose") or _n.startswith("test_flip") or _n.startswith("test_transverse"):
        if callable(_f):
            run(_n, _f)


# ===================================================================
# Tests/test_image_convert.py — mode conversion
# ===================================================================
print("\n--- test_image_convert ---")


def test_convert_RGB_to_L():
    im = hopper("RGB")
    out = im.convert("L")
    assert_image(out, "L", im.size)

def test_convert_RGB_to_RGBA():
    im = hopper("RGB")
    out = im.convert("RGBA")
    assert_image(out, "RGBA", im.size)

def test_convert_RGB_to_LA():
    im = hopper("RGB")
    out = im.convert("LA")
    assert_image(out, "LA", im.size)

def test_convert_L_to_RGB():
    im = hopper("L")
    out = im.convert("RGB")
    assert_image(out, "RGB", im.size)

def test_convert_L_to_RGBA():
    im = hopper("L")
    out = im.convert("RGBA")
    assert_image(out, "RGBA", im.size)

def test_convert_RGBA_to_RGB():
    im = hopper("RGBA")
    out = im.convert("RGB")
    assert_image(out, "RGB", im.size)

def test_convert_RGBA_to_L():
    im = hopper("RGBA")
    out = im.convert("L")
    assert_image(out, "L", im.size)

def test_convert_preserves_size():
    for src in ("L", "RGB", "RGBA"):
        for dst in ("L", "RGB", "RGBA"):
            im = hopper(src)
            out = im.convert(dst)
            assert out.size == im.size, f"{src}→{dst} changed size"

def test_convert_noop():
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
    """RGB→RGBA should set alpha to 255."""
    im = Image.new("RGB", (1, 1), (100, 150, 200))
    out = im.convert("RGBA")
    r, g, b, a = out.getpixel((0, 0))
    assert a == 255
    assert (r, g, b) == (100, 150, 200)


for _n, _f in list(locals().items()):
    if _n.startswith("test_convert") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_copy.py — copy
# ===================================================================
print("\n--- test_image_copy ---")


def test_copy_RGB():
    im = hopper("RGB")
    out = im.copy()
    assert_image(out, im.mode, im.size)

def test_copy_L():
    im = hopper("L")
    out = im.copy()
    assert_image(out, im.mode, im.size)

def test_copy_RGBA():
    im = hopper("RGBA")
    out = im.copy()
    assert_image(out, im.mode, im.size)

def test_copy_independence():
    """Modifying the copy must not affect the original."""
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    out = im.copy()
    out.putpixel((0, 0), (99, 99, 99))
    assert im.getpixel((0, 0)) == (1, 2, 3)
    assert out.getpixel((0, 0)) == (99, 99, 99)

def test_copy_equal():
    im = hopper("RGB")
    out = im.copy()
    assert_image_equal(im, out)

def test_copy_of_crop():
    im = hopper("RGB")
    cropped = im.crop((10, 10, 20, 20))
    out = cropped.copy()
    assert_image(out, im.mode, (10, 10))


for _n, _f in list(locals().items()):
    if _n.startswith("test_copy") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_image_access.py — getpixel / putpixel
# ===================================================================
print("\n--- test_image_access ---")


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

def test_getpixel_default_black_RGB():
    im = Image.new("RGB", (10, 10))
    assert im.getpixel((5, 5)) == (0, 0, 0)

def test_getpixel_default_black_L():
    im = Image.new("L", (10, 10))
    assert im.getpixel((5, 5)) == 0

def test_putpixel_getpixel_all_corners():
    im = Image.new("RGB", (10, 10))
    corners = [(0, 0), (9, 0), (0, 9), (9, 9)]
    for i, (x, y) in enumerate(corners):
        c = (i * 60, i * 60 + 10, i * 60 + 20)
        im.putpixel((x, y), c)
    for i, (x, y) in enumerate(corners):
        c = (i * 60, i * 60 + 10, i * 60 + 20)
        assert im.getpixel((x, y)) == c, f"corner ({x},{y}) mismatch"

def test_putpixel_getpixel_scan():
    """Adapted from test_image_access: full image putpixel/getpixel roundtrip."""
    im1 = Image.new("RGB", (16, 16))
    # Fill with a pattern
    for y in range(16):
        for x in range(16):
            im1.putpixel((x, y), (x * 16, y * 16, (x + y) * 8))
    # Read back
    for y in range(16):
        for x in range(16):
            expected = (x * 16, y * 16, (x + y) * 8)
            actual = im1.getpixel((x, y))
            assert actual == expected, f"({x},{y}): expected {expected}, got {actual}"


for _n, _f in list(locals().items()):
    if _n.startswith("test_getpixel") or _n.startswith("test_putpixel"):
        if callable(_f):
            run(_n, _f)


# ===================================================================
# Tests/test_image_filter.py — filters
# ===================================================================
print("\n--- test_image_filter ---")


def test_filter_blur_RGB():
    im = hopper("RGB")
    out = im.filter(ImageFilter.BLUR)
    assert_image(out, "RGB", im.size)

def test_filter_blur_L():
    im = hopper("L")
    out = im.filter(ImageFilter.BLUR)
    assert_image(out, "L", im.size)

def test_filter_sharpen_RGB():
    im = hopper("RGB")
    out = im.filter(ImageFilter.SHARPEN)
    assert_image(out, "RGB", im.size)

def test_filter_sharpen_L():
    im = hopper("L")
    out = im.filter(ImageFilter.SHARPEN)
    assert_image(out, "L", im.size)

def test_filter_smooth_RGB():
    im = hopper("RGB")
    out = im.filter(ImageFilter.SMOOTH)
    assert_image(out, "RGB", im.size)

def test_filter_gaussian_blur_default():
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur())
    assert_image(out, "RGB", im.size)

def test_filter_gaussian_blur_radius_5():
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur(5))
    assert_image(out, "RGB", im.size)

def test_filter_preserves_mode():
    for mode in ("L", "RGB"):
        for filt in (ImageFilter.BLUR, ImageFilter.SHARPEN, ImageFilter.SMOOTH):
            im = hopper(mode)
            out = im.filter(filt)
            assert out.mode == mode, f"{filt.name} changed mode from {mode} to {out.mode}"

def test_filter_small_image():
    """Adapted from test_image_filter: crash test on small images."""
    im = Image.new("RGB", (3, 3), (100, 100, 100))
    out = im.filter(ImageFilter.SMOOTH)
    assert_image(out, "RGB", (3, 3))

def test_filter_1x1():
    im = Image.new("RGB", (1, 1), (50, 60, 70))
    out = im.filter(ImageFilter.BLUR)
    assert_image(out, "RGB", (1, 1))


for _n, _f in list(locals().items()):
    if _n.startswith("test_filter") and callable(_f):
        run(_n, _f)


# ===================================================================
# Tests/test_imagedraw.py — ImageDraw
# ===================================================================
print("\n--- test_imagedraw ---")

W, H = 100, 100
X0, Y0 = 25, 25
X1, Y1 = 75, 75


def test_draw_sanity():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(255, 0, 0))

def test_draw_rectangle_fill():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(255, 0, 0))
    # Centre pixel should be red
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Outside should be black
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_draw_rectangle_outline():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], outline=(0, 255, 0))
    # Edge pixel should be green
    assert im.getpixel((X0, Y0)) == (0, 255, 0)
    assert im.getpixel((X1, Y0)) == (0, 255, 0)
    # Centre should remain black (outline only, no fill)
    assert im.getpixel((50, 50)) == (0, 0, 0)

def test_draw_rectangle_flat_coords():
    """Pillow accepts (x0, y0, x1, y1) as a flat tuple."""
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([X0, Y0, X1, Y1], fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)

def test_draw_rectangle_list_of_tuples():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(128, 128, 128))
    assert im.getpixel((50, 50)) == (128, 128, 128)

def test_draw_big_rectangle():
    """Adapted from test_imagedraw: rectangle larger than image."""
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(-1, -1), (W + 1, H + 1)], fill=(255, 128, 0))
    # Every pixel should be filled
    assert im.getpixel((0, 0)) == (255, 128, 0)
    assert im.getpixel((W - 1, H - 1)) == (255, 128, 0)

def test_draw_line_basic():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([(10, 10), (90, 10)], fill=(255, 255, 0))
    # Pixel on the line
    assert im.getpixel((50, 10)) == (255, 255, 0)
    # Pixel off the line
    assert im.getpixel((50, 50)) == (0, 0, 0)

def test_draw_line_vertical():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([(50, 10), (50, 90)], fill=(0, 255, 255))
    assert im.getpixel((50, 50)) == (0, 255, 255)

def test_draw_line_diagonal():
    im = Image.new("RGB", (20, 20))
    draw = ImageDraw.Draw(im)
    draw.line([(0, 0), (19, 19)], fill=(255, 0, 255))
    assert im.getpixel((10, 10)) == (255, 0, 255)

def test_draw_line_flat_coords():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([10, 50, 90, 50], fill=(100, 200, 100))
    assert im.getpixel((50, 50)) == (100, 200, 100)

def test_draw_line_width():
    im = Image.new("RGB", (20, 20))
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (14, 10)], fill=(255, 0, 0), width=3)
    # Middle of the line, one pixel above and below should also be drawn
    assert im.getpixel((10, 10)) == (255, 0, 0)
    assert im.getpixel((10, 9)) == (255, 0, 0)

def test_draw_multiple():
    """Draw multiple shapes and verify they don't interfere."""
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (30, 30)], fill=(255, 0, 0))
    draw.rectangle([(50, 50), (70, 70)], fill=(0, 0, 255))
    assert im.getpixel((20, 20)) == (255, 0, 0)
    assert im.getpixel((60, 60)) == (0, 0, 255)
    assert im.getpixel((40, 40)) == (0, 0, 0)


def test_draw_ellipse_fill():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(20, 20), (80, 80)], fill=(255, 0, 0))
    # Centre of ellipse should be red
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Corner should be black (outside ellipse)
    assert im.getpixel((0, 0)) == (0, 0, 0)

def test_draw_ellipse_outline():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(20, 20), (80, 80)], outline=(0, 255, 0))
    # Centre should remain black (outline only)
    assert im.getpixel((50, 50)) == (0, 0, 0)
    # Top of ellipse should be green (around y=20, x=50)
    assert im.getpixel((50, 20)) == (0, 255, 0)

def test_draw_text_basic():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.text((10, 10), "Hi", fill=(255, 255, 0))
    # Some pixel in the text region should be yellow
    found = False
    for y in range(10, 26):
        for x in range(10, 30):
            if im.getpixel((x, y)) == (255, 255, 0):
                found = True
                break
        if found:
            break
    assert found, "text pixels not found"

def test_draw_text_center_anchor():
    im = Image.new("RGB", (200, 50))
    draw = ImageDraw.Draw(im)
    draw.text((100, 10), "AB", fill=(255, 0, 0), anchor="center")
    # Text centred at x=100: 2 chars × 8px = 16px wide, so from 92 to 108
    found = False
    for x in range(90, 110):
        if im.getpixel((x, 14)) == (255, 0, 0):
            found = True
            break
    assert found, "centred text pixels not found"

def test_draw_text_right_anchor():
    im = Image.new("RGB", (200, 50))
    draw = ImageDraw.Draw(im)
    draw.text((100, 10), "AB", fill=(0, 255, 0), anchor="right")
    # Text right-aligned at x=100: 2 chars × 8px = 16px, so from 84 to 100
    found = False
    for x in range(82, 100):
        if im.getpixel((x, 14)) == (0, 255, 0):
            found = True
            break
    assert found, "right-anchored text pixels not found"

def test_draw_text_scaled():
    im = Image.new("RGB", (200, 100))
    draw = ImageDraw.Draw(im)

    class FakeFont:
        size = 20

    draw.text((10, 10), "A", fill=(0, 0, 255), font=FakeFont())
    # Scaled text (16×32) should have blue pixels in a wider area
    found = False
    for y in range(10, 42):
        for x in range(10, 26):
            if im.getpixel((x, y)) == (0, 0, 255):
                found = True
                break
        if found:
            break
    assert found, "scaled text pixels not found"


for _n, _f in list(locals().items()):
    if _n.startswith("test_draw") and callable(_f):
        run(_n, _f)


# ===================================================================
# Combined / integration tests
# ===================================================================
print("\n--- integration ---")


def test_chain_operations():
    """Create → resize → crop → rotate → convert → save → open."""
    im = Image.new("RGB", (200, 100), (50, 100, 150))
    im = im.resize((100, 50))
    im = im.crop((10, 10, 60, 40))
    im = im.rotate(90)
    im = im.convert("L")
    im.save("/tmp/_pil_chain.png")
    im2 = Image.open("/tmp/_pil_chain.png")
    assert im2.mode == "L"
    # After resize(100,50) → crop gives (50,30) → rotate90 gives (30,50)
    assert im2.size == (30, 50)

def test_draw_then_save():
    im = Image.new("RGB", (50, 50), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (40, 40)], fill=(0, 0, 0))
    im.save("/tmp/_pil_draw.png")
    im2 = Image.open("/tmp/_pil_draw.png")
    assert im2.getpixel((25, 25)) == (0, 0, 0)
    assert im2.getpixel((0, 0)) == (255, 255, 255)

def test_filter_then_save():
    im = hopper("RGB")
    blurred = im.filter(ImageFilter.GaussianBlur(3))
    blurred.save("/tmp/_pil_blur.png")
    im2 = Image.open("/tmp/_pil_blur.png")
    assert_image(im2, "RGB", im.size)

def test_multiformat_save():
    """Save in each supported format and reopen."""
    im = Image.new("RGB", (10, 10), (33, 66, 99))
    for fmt in ("png", "bmp", "gif", "tiff"):
        path = f"/tmp/_pil_fmt.{fmt}"
        im.save(path, fmt)
        im2 = Image.open(path)
        assert_image(im2, im2.mode, (10, 10))

def test_jpeg_save_reopen():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    im.save("/tmp/_pil_fmt.jpg", "jpeg")
    im2 = Image.open("/tmp/_pil_fmt.jpg")
    assert im2.size == (10, 10)

def test_open_bytes():
    """Open from bytes rather than a file path."""
    im = Image.new("RGB", (5, 5), (42, 42, 42))
    data = _pil_native.image_save(im._handle, "png")
    im2 = Image.open(data)
    assert im2.size == (5, 5)
    assert im2.getpixel((0, 0)) == (42, 42, 42)


for _n, _f in list(locals().items()):
    if _n.startswith("test_chain") or _n.startswith("test_multi") or _n.startswith("test_jpeg") or _n.startswith("test_open"):
        if callable(_f):
            run(_n, _f)

# Also re-run the two draw_then / filter_then
run("test_draw_then_save", test_draw_then_save)
run("test_filter_then_save", test_filter_then_save)

# ===================================================================
# Summary
# ===================================================================
print(f"\n{'=' * 40}")
print(f"  {_pass} passed, {_fail} failed")
print(f"{'=' * 40}")
if _fail:
    raise SystemExit(1)
