"""Tests for ImageFilter — exact behavior on known input patterns."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageFilter


# ---------------------------------------------------------------------------
# Edge detection on known patterns
# ---------------------------------------------------------------------------

def test_find_edges_on_step_edge():
    """FIND_EDGES on step function should produce nonzero at edge."""
    im = Image.new("L", (20, 10), 0)
    # Left half black, right half white
    for y in range(10):
        for x in range(10, 20):
            im.putpixel((x, y), 255)
    out = im.filter(ImageFilter.FIND_EDGES)
    # Should have high values at the step edge (x=9-10)
    edge_val = max(out.getpixel((9, 5)), out.getpixel((10, 5)))
    assert edge_val > 50


def test_find_edges_flat_region():
    """FIND_EDGES on flat region → near zero."""
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.FIND_EDGES)
    assert out.getpixel((10, 10)) <= 20


def test_contour_flat_region():
    """CONTOUR on flat region → near uniform value."""
    im = Image.new("L", (20, 20), 100)
    out = im.filter(ImageFilter.CONTOUR)
    # Contour on flat region should be near uniform
    v1 = out.getpixel((5, 5))
    v2 = out.getpixel((15, 15))
    assert abs(v1 - v2) <= 20


# ---------------------------------------------------------------------------
# Blur reduces differences
# ---------------------------------------------------------------------------

def test_blur_reduces_extreme_values():
    """Blurring an image with extreme values should bring them closer."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)  # single bright pixel
    out = im.filter(ImageFilter.BLUR)
    # Center pixel should be less bright after blur
    center = out.getpixel((5, 5))
    assert center < 255


def test_blur_spreads_to_neighbors():
    """Blur should spread bright pixel to neighbors."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)
    out = im.filter(ImageFilter.BLUR)
    # Neighbor pixels should now be > 0
    neighbor = out.getpixel((4, 5))
    assert neighbor > 0


# ---------------------------------------------------------------------------
# Sharpen increases contrast
# ---------------------------------------------------------------------------

def test_sharpen_uniform_unchanged():
    """Sharpening uniform image changes nothing."""
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.SHARPEN)
    assert abs(out.getpixel((10, 10)) - 128) <= 10


def test_sharpen_edge_increases():
    """Sharpening an edge should increase its contrast."""
    im = Image.new("L", (20, 10), 0)
    for y in range(10):
        for x in range(10, 20):
            im.putpixel((x, y), 200)
    out = im.filter(ImageFilter.SHARPEN)
    # Sharpened image should have more contrast at edge
    v_dark = out.getpixel((5, 5))
    v_bright = out.getpixel((15, 5))
    assert v_bright > v_dark


# ---------------------------------------------------------------------------
# GaussianBlur radius effects
# ---------------------------------------------------------------------------

def test_gaussian_blur_larger_radius_more_blur():
    """Larger radius should blur more."""
    im = Image.new("L", (30, 30), 0)
    im.putpixel((15, 15), 255)
    out1 = im.filter(ImageFilter.GaussianBlur(1))
    out2 = im.filter(ImageFilter.GaussianBlur(5))
    # With larger radius, center should be less bright
    v1 = out1.getpixel((15, 15))
    v2 = out2.getpixel((15, 15))
    assert v2 <= v1


def test_gaussian_blur_1_uniform():
    im = Image.new("L", (20, 20), 128)
    out = im.filter(ImageFilter.GaussianBlur(1))
    assert abs(out.getpixel((10, 10)) - 128) <= 5


# ---------------------------------------------------------------------------
# MinFilter and MaxFilter exact behavior
# ---------------------------------------------------------------------------

def test_min_filter_on_isolated_bright_pixel():
    """MinFilter should eliminate isolated bright pixels."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)  # isolated bright pixel
    out = im.filter(ImageFilter.MinFilter(3))
    # The bright pixel should be eliminated (surrounded by 0s, min=0)
    assert out.getpixel((5, 5)) == 0


def test_max_filter_on_isolated_dark_pixel():
    """MaxFilter should eliminate isolated dark pixels."""
    im = Image.new("L", (10, 10), 255)
    im.putpixel((5, 5), 0)  # isolated dark pixel
    out = im.filter(ImageFilter.MaxFilter(3))
    # The dark pixel should be eliminated (surrounded by 255s, max=255)
    assert out.getpixel((5, 5)) == 255


def test_median_filter_uniform():
    im = Image.new("L", (10, 10), 100)
    out = im.filter(ImageFilter.MedianFilter(3))
    assert out.getpixel((5, 5)) == 100


def test_rank_filter_min():
    """RankFilter with rank=0 is same as MinFilter."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)
    # 3x3 area, rank=0 → minimum
    out = im.filter(ImageFilter.RankFilter(3, 0))
    assert out.getpixel((5, 5)) == 0


# ---------------------------------------------------------------------------
# Kernel filter
# ---------------------------------------------------------------------------

def test_kernel_identity():
    """3x3 identity kernel should leave image unchanged (approximately)."""
    im = Image.new("L", (10, 10), 128)
    # Identity kernel: center=1, rest=0
    kernel = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[0, 0, 0, 0, 1, 0, 0, 0, 0],
        scale=1,
    )
    out = im.filter(kernel)
    # Interior should be unchanged
    assert abs(out.getpixel((5, 5)) - 128) <= 5


def test_kernel_uniform():
    """3x3 averaging kernel should leave uniform image unchanged."""
    im = Image.new("L", (10, 10), 100)
    kernel = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[1, 1, 1, 1, 1, 1, 1, 1, 1],
        scale=9,
    )
    out = im.filter(kernel)
    assert abs(out.getpixel((5, 5)) - 100) <= 3


if __name__ == "__main__":
    pytest.main()
