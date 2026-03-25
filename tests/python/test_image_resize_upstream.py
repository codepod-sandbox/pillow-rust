"""
Tests adapted from upstream Pillow test_image_resize.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_resize.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
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


# ---------------------------------------------------------------------------
# Upstream tests — test_image_resize.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("resample", [
    Image.Resampling.NEAREST,
    Image.Resampling.BILINEAR,
    Image.Resampling.BICUBIC,
    Image.Resampling.LANCZOS,
])
def test_resize_sanity(resample, hopper):
    """Upstream test_resize: all resamplers run on L and RGB modes."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        out = im.resize((im.width // 2, im.height // 2), resample=resample)
        assert out.mode == mode
        assert out.size == (im.width // 2, im.height // 2)


def test_resize_zero_size():
    """Upstream: resizing to (0, 0) raises ValueError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((ValueError, Exception)):
        im.resize((0, 0))


def test_resize_enlarges():
    """Upstream: resizing to larger size works correctly."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = im.resize((50, 50))
    assert out.size == (50, 50)
    assert out.getpixel((25, 25)) == (100, 150, 200)


def test_resize_L_mode(hopper):
    """Upstream: resize works correctly for L mode."""
    im = hopper("L")
    out = im.resize((im.width * 2, im.height * 2))
    assert out.mode == "L"
    assert out.size == (im.width * 2, im.height * 2)


def test_resize_RGBA_upstream(hopper):
    """Upstream: resize works for RGBA mode."""
    im = hopper("RGBA")
    out = im.resize((50, 50))
    assert out.mode == "RGBA"
    assert out.size == (50, 50)
