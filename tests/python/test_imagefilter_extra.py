"""Tests for additional ImageFilter types."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageFilter


def _make_test_image():
    """Create a simple test image with some detail."""
    im = Image.new("RGB", (50, 50), (100, 100, 100))
    im.putpixel((25, 25), (255, 0, 0))
    im.putpixel((26, 25), (0, 255, 0))
    im.putpixel((25, 26), (0, 0, 255))
    return im


def test_contour():
    im = _make_test_image()
    out = im.filter(ImageFilter.CONTOUR)
    assert out.size == im.size

def test_detail():
    im = _make_test_image()
    out = im.filter(ImageFilter.DETAIL)
    assert out.size == im.size

def test_edge_enhance():
    im = _make_test_image()
    out = im.filter(ImageFilter.EDGE_ENHANCE)
    assert out.size == im.size

def test_edge_enhance_more():
    im = _make_test_image()
    out = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
    assert out.size == im.size

def test_emboss():
    im = _make_test_image()
    out = im.filter(ImageFilter.EMBOSS)
    assert out.size == im.size
    # Emboss of uniform area should produce ~128 (offset)
    r, g, b = out.getpixel((0, 0))
    assert 120 < r < 140

def test_find_edges():
    im = _make_test_image()
    out = im.filter(ImageFilter.FIND_EDGES)
    assert out.size == im.size

def test_smooth_more():
    im = _make_test_image()
    out = im.filter(ImageFilter.SMOOTH_MORE)
    assert out.size == im.size

def test_unsharp_mask():
    im = _make_test_image()
    out = im.filter(ImageFilter.UnsharpMask(2, 150, 3))
    assert out.size == im.size

def test_gaussian_blur():
    im = _make_test_image()
    out = im.filter(ImageFilter.GaussianBlur(5))
    assert out.size == im.size

def test_median_filter():
    im = _make_test_image()
    out = im.filter(ImageFilter.MedianFilter(3))
    assert out.size == im.size

def test_min_filter():
    im = _make_test_image()
    out = im.filter(ImageFilter.MinFilter(3))
    assert out.size == im.size

def test_max_filter():
    im = _make_test_image()
    out = im.filter(ImageFilter.MaxFilter(3))
    assert out.size == im.size

def test_kernel():
    im = _make_test_image()
    k = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 5, -1, 0, -1, 0])
    out = im.filter(k)
    assert out.size == im.size

def test_kernel_wrong_size():
    with pytest.raises(ValueError):
        ImageFilter.Kernel((5, 5), [1] * 25)


if __name__ == "__main__":
    pytest.main()
