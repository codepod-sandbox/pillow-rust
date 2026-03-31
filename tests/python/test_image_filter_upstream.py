"""
Tests adapted from upstream Pillow test_image_filter.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_filter.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageFilter
from helper import hopper


def test_sanity():
    """All builtin filters run without error on L and RGB — from upstream."""
    builtin_filters = [
        ImageFilter.BLUR,
        ImageFilter.CONTOUR,
        ImageFilter.DETAIL,
        ImageFilter.EDGE_ENHANCE,
        ImageFilter.EDGE_ENHANCE_MORE,
        ImageFilter.EMBOSS,
        ImageFilter.FIND_EDGES,
        ImageFilter.SMOOTH,
        ImageFilter.SMOOTH_MORE,
        ImageFilter.SHARPEN,
    ]
    for mode in ("L", "RGB"):
        im = hopper(mode)
        for f in builtin_filters:
            out = im.filter(f)
            assert out.mode == im.mode
            assert out.size == im.size


def test_sanity_rank_filters():
    """Rank filters run without error on L — from upstream."""
    rank_filters = [
        ImageFilter.MaxFilter(),
        ImageFilter.MedianFilter(),
        ImageFilter.MinFilter(),
    ]
    im = hopper("L")
    for f in rank_filters:
        out = im.filter(f)
        assert out.mode == im.mode
        assert out.size == im.size


def test_sanity_gaussian_blur():
    """GaussianBlur variants run without error — from upstream."""
    for radius in (0, 5):
        f = ImageFilter.GaussianBlur(radius)
        for mode in ("L", "RGB"):
            im = hopper(mode)
            out = im.filter(f)
            assert out.mode == im.mode
            assert out.size == im.size


def test_sanity_box_blur():
    """BoxBlur variants run without error — from upstream."""
    for radius in (0, 5):
        f = ImageFilter.BoxBlur(radius)
        for mode in ("L", "RGB"):
            im = hopper(mode)
            out = im.filter(f)
            assert out.mode == im.mode
            assert out.size == im.size


def test_sanity_unsharp_mask():
    """UnsharpMask runs without error — from upstream."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        out = im.filter(ImageFilter.UnsharpMask())
        assert out.mode == im.mode
        assert out.size == im.size

        out = im.filter(ImageFilter.UnsharpMask(10))
        assert out.mode == im.mode
        assert out.size == im.size


def test_sanity_error():
    """Filtering with a non-filter raises an error — from upstream."""
    im = hopper("L")
    try:
        im.filter("hello")
        raise AssertionError("Expected TypeError or AttributeError")
    except (TypeError, AttributeError):
        pass


def test_crash():
    """Filters don't crash on small images — from upstream."""
    for size in ((1, 1), (2, 2), (3, 3)):
        im = Image.new("RGB", size)
        im.filter(ImageFilter.SMOOTH)


def test_rankfilter():
    """Min/Median/Max filters return correct values — from upstream."""
    im = Image.new("L", (3, 3))
    im.putdata(list(range(9)))
    # image is:
    #   0 1 2
    #   3 4 5
    #   6 7 8
    minimum = im.filter(ImageFilter.MinFilter()).getpixel((1, 1))
    med = im.filter(ImageFilter.MedianFilter()).getpixel((1, 1))
    maximum = im.filter(ImageFilter.MaxFilter()).getpixel((1, 1))
    assert (minimum, med, maximum) == (0, 4, 8)


def test_rankfilter_properties():
    """RankFilter exposes size and rank — from upstream."""
    rankfilter = ImageFilter.RankFilter(1, 2)
    assert rankfilter.size == 1
    assert rankfilter.rank == 2


def test_kernel_not_enough_coefficients():
    """Kernel with too few coefficients raises ValueError — from upstream."""
    try:
        ImageFilter.Kernel((3, 3), (0, 0))
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_rankfilter_kernel_properties():
    """RankFilter size and rank are accessible — from upstream."""
    rankfilter = ImageFilter.RankFilter(3, 4)
    assert rankfilter.size == 3
    assert rankfilter.rank == 4


if __name__ == "__main__":
    pytest.main()
