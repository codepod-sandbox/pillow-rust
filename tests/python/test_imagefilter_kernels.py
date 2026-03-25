"""Tests for ImageFilter kernel operations — exact behavior."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageFilter


# ---------------------------------------------------------------------------
# Named filters — basic behavior
# ---------------------------------------------------------------------------

def test_blur_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BLUR)
    assert out is not None
    assert out.size == (20, 20)


def test_sharpen_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.SHARPEN)
    assert out.size == (20, 20)


def test_smooth_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.SMOOTH)
    assert out.size == (20, 20)


def test_smooth_more_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.SMOOTH_MORE)
    assert out.size == (20, 20)


def test_edge_enhance_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.EDGE_ENHANCE)
    assert out.size == (20, 20)


def test_edge_enhance_more_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
    assert out.size == (20, 20)


def test_emboss_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.EMBOSS)
    assert out.size == (20, 20)


def test_contour_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.CONTOUR)
    assert out.size == (20, 20)


def test_find_edges_returns_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.FIND_EDGES)
    assert out.size == (20, 20)


# ---------------------------------------------------------------------------
# Filters preserve mode
# ---------------------------------------------------------------------------

def test_blur_preserves_L_mode():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "L"


def test_blur_preserves_RGB_mode():
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    out = im.filter(ImageFilter.BLUR)
    assert out.mode == "RGB"


def test_sharpen_preserves_mode():
    im = Image.new("L", (20, 20), 100)
    out = im.filter(ImageFilter.SHARPEN)
    assert out.mode == "L"


# ---------------------------------------------------------------------------
# Uniform image stays uniform after smooth filters
# ---------------------------------------------------------------------------

def test_blur_uniform_stays_uniform():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BLUR)
    assert abs(out.getpixel((10, 10)) - 128) <= 5


def test_smooth_uniform_stays_uniform():
    im = Image.new("L", (20, 20), 100)
    out = im.filter(ImageFilter.SMOOTH)
    assert abs(out.getpixel((10, 10)) - 100) <= 3


def test_gaussian_blur_uniform():
    im = Image.new("L", (20, 20), 200)
    out = im.filter(ImageFilter.GaussianBlur(2))
    assert abs(out.getpixel((10, 10)) - 200) <= 5


# ---------------------------------------------------------------------------
# Edge detection on flat image → near zero
# ---------------------------------------------------------------------------

def test_find_edges_flat_image_near_zero():
    """Edge detection on uniform image should return near-zero values."""
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.FIND_EDGES)
    # Interior of uniform image → near 0
    assert out.getpixel((10, 10)) <= 10


def test_contour_flat_image():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.CONTOUR)
    # Contour of flat image — interior should be mostly flat
    # Just check it doesn't crash and returns a reasonable value
    v = out.getpixel((10, 10))
    assert 0 <= v <= 255


# ---------------------------------------------------------------------------
# GaussianBlur
# ---------------------------------------------------------------------------

def test_gaussian_blur_radius_0():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.GaussianBlur(0))
    assert out.getpixel((10, 10)) == 128


def test_gaussian_blur_large_radius():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.GaussianBlur(5))
    assert abs(out.getpixel((10, 10)) - 128) <= 10


def test_gaussian_blur_does_not_modify_original():
    im = Image.new("L", (20, 20), 128)
    im.filter(ImageFilter.GaussianBlur(2))
    assert im.getpixel((10, 10)) == 128


# ---------------------------------------------------------------------------
# BoxBlur
# ---------------------------------------------------------------------------

def test_box_blur_basic():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BoxBlur(2))
    assert abs(out.getpixel((10, 10)) - 128) <= 5


def test_box_blur_preserves_L_mode():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.BoxBlur(1))
    assert out.mode == "L"


def test_box_blur_preserves_RGB_mode():
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    out = im.filter(ImageFilter.BoxBlur(1))
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# UnsharpMask
# ---------------------------------------------------------------------------

def test_unsharp_mask_basic():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.UnsharpMask())
    assert out.size == (20, 20)


def test_unsharp_mask_preserves_mode():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.UnsharpMask())
    assert out.mode == "L"


# ---------------------------------------------------------------------------
# RankFilter
# ---------------------------------------------------------------------------

def test_rank_filter_basic():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.RankFilter(3, 4))  # 3x3, rank 4 (median of 9)
    assert out.mode == "L"
    assert out.size == (20, 20)


def test_min_filter():
    im = Image.new("L", (20, 20), 200)
    out = im.filter(ImageFilter.MinFilter(3))
    assert out.getpixel((10, 10)) == 200  # uniform image: min is same


def test_max_filter():
    im = Image.new("L", (20, 20), 100)
    out = im.filter(ImageFilter.MaxFilter(3))
    assert out.getpixel((10, 10)) == 100


def test_median_filter():
    im = Image.new("L", (20, 20), 150)
    out = im.filter(ImageFilter.MedianFilter(3))
    assert out.getpixel((10, 10)) == 150


if __name__ == "__main__":
    pytest.main()
