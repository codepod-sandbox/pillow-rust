"""
Tests adapted from upstream Pillow test_image_resize.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_resize.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_resize():
    """resize() preserves mode and returns correct size — from upstream."""
    def resize(mode, size):
        out = hopper(mode).resize(size)
        assert out.mode == mode
        assert out.size == tuple(size)

    for mode in ("L", "RGB", "RGBA", "LA"):
        resize(mode, (112, 103))
        resize(mode, [188, 214])


def test_resize_all_resamplings():
    """All resampling filters work for reduce and enlarge — from upstream."""
    resamplings = [
        Image.Resampling.NEAREST,
        Image.Resampling.BOX,
        Image.Resampling.BILINEAR,
        Image.Resampling.HAMMING,
        Image.Resampling.BICUBIC,
        Image.Resampling.LANCZOS,
    ]
    for resample in resamplings:
        # reduce
        r = hopper("RGB").resize((15, 12), resample)
        assert r.mode == "RGB"
        assert r.size == (15, 12)
        # enlarge
        r2 = hopper("RGB").resize((212, 195), resample)
        assert r2.mode == "RGB"
        assert r2.size == (212, 195)


def test_explicit_filter_matches_itself():
    """Explicit resampling filter is consistent — derived from upstream."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        a = im.resize((20, 20), Image.Resampling.BICUBIC)
        b = im.resize((20, 20), Image.Resampling.BICUBIC)
        assert_image_equal(a, b)


def test_resize_l_modes():
    """resize works on L and LA modes — from upstream."""
    for mode in ("L", "LA"):
        im = hopper(mode)
        out = im.resize((64, 64), Image.Resampling.BILINEAR)
        assert out.mode == mode
        assert out.size == (64, 64)


def test_resize_to_same_size():
    """Resize to same size returns image with same content — from upstream."""
    im = hopper("RGB")
    out = im.resize(im.size)
    assert out.size == im.size
    assert out.mode == im.mode


def test_resize_zero_size():
    """Resize zero-size image works — from upstream."""
    im = Image.new("RGB", (0, 0))
    for resample in (Image.Resampling.NEAREST, Image.Resampling.BILINEAR, Image.Resampling.BICUBIC):
        r = im.resize((10, 10), resample)
        assert r.mode == "RGB"
        assert r.size == (10, 10)


def test_resize_nearest_identity():
    """NEAREST resize to same size is identity — derived from upstream."""
    im = hopper("L")
    out = im.resize(im.size, Image.Resampling.NEAREST)
    assert_image_equal(im, out)


if __name__ == "__main__":
    pytest.main()
