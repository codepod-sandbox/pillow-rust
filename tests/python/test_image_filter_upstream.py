"""
Tests adapted from upstream Pillow test_image_filter.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_filter.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image, ImageFilter
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# Filter sanity: apply every filter to L and RGB modes
# ---------------------------------------------------------------------------


def test_blur_L(hopper):
    im = hopper("L")
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "L"
    assert out.size == im.size


def test_blur_RGB(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_sharpen_L(hopper):
    im = hopper("L")
    out = im.filter(ImageFilter.SHARPEN)
    assert out.mode == "L"
    assert out.size == im.size


def test_sharpen_RGB(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.SHARPEN)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_smooth_L(hopper):
    im = hopper("L")
    out = im.filter(ImageFilter.SMOOTH)
    assert out.mode == "L"
    assert out.size == im.size


def test_smooth_RGB(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.SMOOTH)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_gaussian_blur_default(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur())
    assert_image(out, "RGB", im.size)


def test_gaussian_blur_radius_0(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur(0))
    assert_image(out, "RGB", im.size)


def test_gaussian_blur_radius_5(hopper):
    im = hopper("RGB")
    out = im.filter(ImageFilter.GaussianBlur(5))
    assert_image(out, "RGB", im.size)


def test_filter_preserves_mode(hopper):
    for mode in ("L", "RGB"):
        for filt in (ImageFilter.BLUR, ImageFilter.SHARPEN, ImageFilter.SMOOTH):
            im = hopper(mode)
            out = im.filter(filt)
            assert out.mode == mode


# ---------------------------------------------------------------------------
# Crash tests — small images
# ---------------------------------------------------------------------------


def test_crash_1x1():
    im = Image.new("RGB", (1, 1))
    im.filter(ImageFilter.SMOOTH)


def test_crash_2x2():
    im = Image.new("RGB", (2, 2))
    im.filter(ImageFilter.SMOOTH)


def test_crash_3x3():
    im = Image.new("RGB", (3, 3))
    im.filter(ImageFilter.SMOOTH)


# ---------------------------------------------------------------------------
# Gaussian blur produces different output than original
# ---------------------------------------------------------------------------


def test_gaussian_blur_changes_image(hopper):
    im = hopper("RGB")
    blurred = im.filter(ImageFilter.GaussianBlur(3))
    # Should be different from original (at least some pixels)
    assert im.tobytes() != blurred.tobytes()


def test_filter_small_image():
    im = Image.new("RGB", (3, 3), (100, 100, 100))
    out = im.filter(ImageFilter.SMOOTH)
    assert_image(out, "RGB", (3, 3))


# ---------------------------------------------------------------------------
# Upstream tests — test_image_filter.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filt", [
    ImageFilter.BLUR,
    ImageFilter.SHARPEN,
    ImageFilter.SMOOTH,
])
def test_sanity_all_filters_L(filt, hopper):
    """Upstream test_sanity: all builtin filters run on L mode images."""
    im = hopper("L")
    out = im.filter(filt)
    assert out.mode == "L"
    assert out.size == im.size


@pytest.mark.parametrize("filt", [
    ImageFilter.BLUR,
    ImageFilter.SHARPEN,
    ImageFilter.SMOOTH,
])
def test_sanity_all_filters_RGB(filt, hopper):
    """Upstream test_sanity: all builtin filters run on RGB mode images."""
    im = hopper("RGB")
    out = im.filter(filt)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_gaussian_blur_radius():
    """Upstream: GaussianBlur accepts a radius parameter."""
    im = Image.new("RGB", (20, 20), (200, 200, 200))
    im.putpixel((10, 10), (0, 0, 0))
    blurred = im.filter(ImageFilter.GaussianBlur(radius=2))
    assert blurred.size == im.size
    assert blurred.mode == "RGB"


def test_gaussian_blur_L(hopper):
    """Upstream: GaussianBlur works on L mode images."""
    im = hopper("L")
    out = im.filter(ImageFilter.GaussianBlur(radius=2))
    assert out.mode == "L"
    assert out.size == im.size
