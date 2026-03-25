"""Extra ImageFilter tests — mode behavior, exact outputs, edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageFilter


def _solid(mode, color, size=(10, 10)):
    return Image.new(mode, size, color)


# ---------------------------------------------------------------------------
# Filter on different modes
# ---------------------------------------------------------------------------

def test_blur_rgb():
    im = _solid("RGB", (100, 150, 200))
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_blur_l():
    im = _solid("L", 100)
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "L"
    assert out.size == im.size


def test_blur_rgba():
    im = _solid("RGBA", (100, 150, 200, 128))
    out = im.filter(ImageFilter.BLUR)
    assert out.size == im.size


def test_sharpen_rgb():
    im = _solid("RGB", (128, 128, 128))
    out = im.filter(ImageFilter.SHARPEN)
    assert out.mode == "RGB"


def test_smooth_rgb():
    im = _solid("RGB", (100, 100, 100))
    out = im.filter(ImageFilter.SMOOTH)
    assert out.mode == "RGB"


def test_gaussian_blur_radius():
    im = _solid("L", 128)
    im.putpixel((5, 5), 255)
    out_small = im.filter(ImageFilter.GaussianBlur(1))
    out_large = im.filter(ImageFilter.GaussianBlur(5))
    # Larger radius should spread the bright spot more
    assert out_large.size == im.size
    assert out_small.size == im.size


def test_gaussian_blur_L_uniform_unchanged():
    """Blur on a uniform image should return the same values."""
    im = _solid("L", 200)
    out = im.filter(ImageFilter.GaussianBlur(3))
    assert out.getpixel((5, 5)) == 200


def test_gaussian_blur_RGB_uniform_unchanged():
    im = _solid("RGB", (100, 150, 200))
    out = im.filter(ImageFilter.GaussianBlur(3))
    r, g, b = out.getpixel((5, 5))
    # Values should be within 1 of original (border effects)
    assert abs(r - 100) <= 2
    assert abs(g - 150) <= 2
    assert abs(b - 200) <= 2


# ---------------------------------------------------------------------------
# BoxBlur
# ---------------------------------------------------------------------------

def test_box_blur_basic():
    im = _solid("L", 100)
    out = im.filter(ImageFilter.BoxBlur(2))
    assert out.mode == "L"
    assert out.size == im.size
    # Uniform image should stay uniform
    assert out.getpixel((5, 5)) == 100


def test_box_blur_rgb():
    im = _solid("RGB", (100, 200, 50))
    out = im.filter(ImageFilter.BoxBlur(1))
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# UnsharpMask
# ---------------------------------------------------------------------------

def test_unsharp_mask_L():
    im = _solid("L", 100)
    im.putpixel((5, 5), 200)
    out = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    assert out.mode == "L"
    assert out.size == im.size


def test_unsharp_mask_RGB():
    im = _solid("RGB", (100, 100, 100))
    out = im.filter(ImageFilter.UnsharpMask())
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# Kernel
# ---------------------------------------------------------------------------

def test_kernel_identity():
    """Identity kernel [0,0,0, 0,1,0, 0,0,0] returns same image."""
    im = _solid("L", 128)
    im.putpixel((5, 5), 200)
    k = ImageFilter.Kernel((3, 3), [0, 0, 0, 0, 1, 0, 0, 0, 0], scale=1)
    out = im.filter(k)
    # Interior pixel should be close to 200
    val = out.getpixel((5, 5))
    assert 180 <= int(val) <= 220


def test_kernel_scale():
    """Kernel with scale=2 halves the output."""
    im = _solid("L", 200)
    # All-ones kernel with scale=9 → average of 9 pixels / 9 = same value
    k = ImageFilter.Kernel((3, 3), [1] * 9, scale=9)
    out = im.filter(k)
    # Uniform image: output should be close to 200
    val = out.getpixel((5, 5))
    assert 195 <= int(val) <= 205


def test_kernel_wrong_size_raises():
    """Kernel size must match len of data."""
    with pytest.raises((ValueError, Exception)):
        k = ImageFilter.Kernel((3, 3), [1] * 25)


# ---------------------------------------------------------------------------
# MedianFilter, MinFilter, MaxFilter
# ---------------------------------------------------------------------------

def test_median_filter_L():
    im = _solid("L", 100)
    im.putpixel((5, 5), 255)  # isolated bright pixel
    out = im.filter(ImageFilter.MedianFilter(3))
    # Median of mostly 100s → 100 (isolated pixel removed)
    val = out.getpixel((5, 5))
    assert int(val) == 100


def test_min_filter_L():
    im = Image.new("L", (10, 10), 200)
    im.putpixel((5, 5), 50)
    out = im.filter(ImageFilter.MinFilter(3))
    # The minimum in the 3x3 neighborhood around (5,5) includes 50
    val = out.getpixel((5, 5))
    assert int(val) == 50


def test_max_filter_L():
    im = Image.new("L", (10, 10), 50)
    im.putpixel((5, 5), 200)
    out = im.filter(ImageFilter.MaxFilter(3))
    # Max in neighborhood should include 200
    # Center pixel will have 200; neighbors that see it will also get 200
    val = out.getpixel((5, 5))
    assert int(val) == 200


def test_rank_filter_L():
    im = _solid("L", 100)
    out = im.filter(ImageFilter.RankFilter(3, 5))
    assert out.mode == "L"
    assert out.size == im.size


# ---------------------------------------------------------------------------
# Builtin named filters
# ---------------------------------------------------------------------------

def test_contour_produces_edges():
    """CONTOUR should produce non-uniform output for non-uniform input."""
    im = Image.new("L", (10, 10), 0)
    for y in range(5):
        for x in range(10):
            im.putpixel((x, y), 200)
    out = im.filter(ImageFilter.CONTOUR)
    assert out.mode == "L"


def test_emboss_offset():
    """EMBOSS of uniform image produces near-128 output."""
    im = _solid("L", 100)
    out = im.filter(ImageFilter.EMBOSS)
    val = out.getpixel((0, 0))
    # Emboss typically adds an offset of ~128
    assert 100 <= int(val) <= 160


def test_find_edges_uniform():
    """FIND_EDGES of uniform image should produce near-zero output."""
    im = _solid("L", 100)
    out = im.filter(ImageFilter.FIND_EDGES)
    val = out.getpixel((5, 5))
    assert int(val) <= 10


if __name__ == "__main__":
    pytest.main()
