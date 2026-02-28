"""
Tests adapted from upstream Pillow test_image_resize.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_resize.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# TestImageResize
# ---------------------------------------------------------------------------


def test_resize_L(hopper):
    out = hopper("L").resize((112, 103))
    assert_image(out, "L", (112, 103))


def test_resize_RGB(hopper):
    out = hopper("RGB").resize((112, 103))
    assert_image(out, "RGB", (112, 103))


def test_resize_RGBA(hopper):
    out = hopper("RGBA").resize((112, 103))
    assert_image(out, "RGBA", (112, 103))


def test_resize_enlarge(hopper):
    out = hopper("RGB").resize((212, 195))
    assert_image(out, "RGB", (212, 195))


def test_resize_down(hopper):
    out = hopper("RGB").resize((15, 12))
    assert_image(out, "RGB", (15, 12))


def test_resize_1x1(hopper):
    out = hopper("RGB").resize((1, 1))
    assert_image(out, "RGB", (1, 1))


def test_resize_preserves_mode(hopper):
    for mode in ("L", "RGB", "RGBA"):
        out = hopper(mode).resize((20, 20))
        assert out.mode == mode


def test_resize_list_size():
    """resize should accept list as well as tuple."""
    im = Image.new("RGB", (10, 10))
    out = im.resize([20, 30])
    assert out.size == (20, 30)


def test_resize_with_resample_nearest():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = im.resize((5, 5), Image.Resampling.NEAREST)
    assert_image(out, "RGB", (5, 5))
    assert out.getpixel((0, 0)) == (255, 0, 0)


def test_resize_with_resample_bilinear():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = im.resize((5, 5), Image.Resampling.BILINEAR)
    assert_image(out, "RGB", (5, 5))


def test_resize_with_resample_bicubic():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = im.resize((5, 5), Image.Resampling.BICUBIC)
    assert_image(out, "RGB", (5, 5))


def test_resize_with_resample_lanczos():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = im.resize((5, 5), Image.Resampling.LANCZOS)
    assert_image(out, "RGB", (5, 5))
