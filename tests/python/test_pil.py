"""Basic PIL tests for the codepod WASM implementation."""


def test_new_image():
    from PIL import Image
    img = Image.new("RGB", (100, 50))
    assert img.size == (100, 50)
    assert img.mode == "RGB"
    print("PASS test_new_image")


def test_new_image_with_color():
    from PIL import Image
    img = Image.new("RGB", (10, 10), (255, 0, 0))
    r, g, b = img.getpixel((0, 0))
    assert r == 255 and g == 0 and b == 0
    print("PASS test_new_image_with_color")


def test_new_grayscale():
    from PIL import Image
    img = Image.new("L", (10, 10), 128)
    assert img.mode == "L"
    val = img.getpixel((5, 5))
    assert val == 128
    print("PASS test_new_grayscale")


def test_getpixel_putpixel():
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    img.putpixel((3, 4), (10, 20, 30))
    assert img.getpixel((3, 4)) == (10, 20, 30)
    print("PASS test_getpixel_putpixel")


def test_resize():
    from PIL import Image
    img = Image.new("RGB", (100, 50))
    resized = img.resize((50, 25))
    assert resized.size == (50, 25)
    print("PASS test_resize")


def test_crop():
    from PIL import Image
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    cropped = img.crop((10, 10, 60, 60))
    assert cropped.size == (50, 50)
    print("PASS test_crop")


def test_rotate_90():
    from PIL import Image
    img = Image.new("RGB", (100, 50))
    rotated = img.rotate(90)
    # 90-degree rotation swaps width and height
    assert rotated.size == (50, 100)
    print("PASS test_rotate_90")


def test_rotate_180():
    from PIL import Image
    img = Image.new("RGB", (100, 50))
    rotated = img.rotate(180)
    assert rotated.size == (100, 50)
    print("PASS test_rotate_180")


def test_convert_rgb_to_l():
    from PIL import Image
    img = Image.new("RGB", (10, 10), (100, 100, 100))
    gray = img.convert("L")
    assert gray.mode == "L"
    assert gray.size == (10, 10)
    print("PASS test_convert_rgb_to_l")


def test_convert_rgb_to_rgba():
    from PIL import Image
    img = Image.new("RGB", (10, 10), (255, 128, 0))
    rgba = img.convert("RGBA")
    assert rgba.mode == "RGBA"
    r, g, b, a = rgba.getpixel((0, 0))
    assert r == 255 and g == 128 and b == 0 and a == 255
    print("PASS test_convert_rgb_to_rgba")


def test_save_load_png():
    from PIL import Image
    img = Image.new("RGB", (10, 10), (42, 43, 44))
    data = _pil_native.image_save(img._handle, "png")
    assert len(data) > 0
    img2 = Image.Image(_pil_native.image_open(data))
    assert img2.size == (10, 10)
    r, g, b = img2.getpixel((0, 0))
    assert r == 42 and g == 43 and b == 44
    print("PASS test_save_load_png")


def test_copy():
    from PIL import Image
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    cp = img.copy()
    cp.putpixel((0, 0), (99, 99, 99))
    # Original should be unchanged
    assert img.getpixel((0, 0)) == (1, 2, 3)
    assert cp.getpixel((0, 0)) == (99, 99, 99)
    print("PASS test_copy")


def test_transpose_flip_lr():
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    img.putpixel((0, 0), (255, 0, 0))
    flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    assert flipped.getpixel((9, 0)) == (255, 0, 0)
    print("PASS test_transpose_flip_lr")


def test_transpose_flip_tb():
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    img.putpixel((0, 0), (0, 255, 0))
    flipped = img.transpose(Image.FLIP_TOP_BOTTOM)
    assert flipped.getpixel((0, 9)) == (0, 255, 0)
    print("PASS test_transpose_flip_tb")


def test_filter_blur():
    from PIL import Image, ImageFilter
    img = Image.new("RGB", (20, 20), (100, 100, 100))
    blurred = img.filter(ImageFilter.BLUR)
    assert blurred.size == (20, 20)
    print("PASS test_filter_blur")


def test_filter_gaussian_blur():
    from PIL import Image, ImageFilter
    img = Image.new("RGB", (20, 20), (100, 100, 100))
    blurred = img.filter(ImageFilter.GaussianBlur(radius=3))
    assert blurred.size == (20, 20)
    print("PASS test_filter_gaussian_blur")


def test_draw_rectangle():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (50, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(5, 5), (15, 15)], fill=(255, 0, 0))
    assert img.getpixel((10, 10)) == (255, 0, 0)
    print("PASS test_draw_rectangle")


def test_tobytes():
    from PIL import Image
    img = Image.new("RGB", (2, 2), (10, 20, 30))
    data = img.tobytes()
    assert isinstance(data, bytes)
    # 2x2 RGB = 12 bytes
    assert len(data) == 12
    print("PASS test_tobytes")


def test_width_height():
    from PIL import Image
    img = Image.new("RGB", (123, 456))
    assert img.width == 123
    assert img.height == 456
    print("PASS test_width_height")


def test_context_manager():
    from PIL import Image
    with Image.new("RGB", (10, 10)) as img:
        assert img.size == (10, 10)
    print("PASS test_context_manager")


# ---- Run all tests ----
test_new_image()
test_new_image_with_color()
test_new_grayscale()
test_getpixel_putpixel()
test_resize()
test_crop()
test_rotate_90()
test_rotate_180()
test_convert_rgb_to_l()
test_convert_rgb_to_rgba()
test_save_load_png()
test_copy()
test_transpose_flip_lr()
test_transpose_flip_tb()
test_filter_blur()
test_filter_gaussian_blur()
test_draw_rectangle()
test_tobytes()
test_width_height()
test_context_manager()
print("ALL TESTS PASSED")
