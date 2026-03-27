"""
Tests adapted from upstream Pillow test_imagestat.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagestat.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageStat
from helper import hopper


def test_sanity():
    """Verify all Stat properties run without error — from upstream."""
    im = hopper()

    st = ImageStat.Stat(im)
    st = ImageStat.Stat(im.histogram())
    st = ImageStat.Stat(im, Image.new("1", im.size, 1))

    # Check these run. Exceptions will cause failures.
    st.extrema
    st.sum
    st.mean
    st.median
    st.rms
    st.sum2
    st.var
    st.stddev


def test_constant():
    """Stat of constant image has known exact values — from upstream."""
    im = Image.new("L", (128, 128), 128)

    st = ImageStat.Stat(im)

    assert st.extrema[0] == (128, 128)
    assert st.sum[0] == 128**3
    assert st.sum2[0] == 128**4
    assert st.mean[0] == 128
    assert st.median[0] == 128
    assert st.rms[0] == 128
    assert st.var[0] == 0
    assert st.stddev[0] == 0


def test_hopper_structure():
    """Verify stat structure for hopper — adapted from upstream.

    Note: exact values differ from upstream because our hopper is
    synthetic, not the real hopper.ppm. We verify structure instead.
    """
    im = hopper()
    st = ImageStat.Stat(im)

    # RGB image should have 3 channels
    assert len(st.extrema) == 3
    assert len(st.sum) == 3
    assert len(st.mean) == 3
    assert len(st.median) == 3
    assert len(st.rms) == 3
    assert len(st.var) == 3
    assert len(st.stddev) == 3

    # Verify ranges are reasonable
    for i in range(3):
        mn, mx = st.extrema[i]
        assert 0 <= mn <= mx <= 255
        assert st.mean[i] >= 0
        assert st.rms[i] >= 0
        assert st.var[i] >= 0
        assert st.stddev[i] >= 0


def test_zero_count():
    """Stat of empty image — from upstream."""
    im = Image.new("L", (0, 0))

    st = ImageStat.Stat(im)

    assert st.mean == [0]
    assert st.rms == [0]
    assert st.var == [0]


def test_l_image():
    """L mode stat has single channel — derived from upstream."""
    im = Image.new("L", (100, 100), 200)
    st = ImageStat.Stat(im)

    assert len(st.count) == 1
    assert st.count[0] == 10000
    assert st.mean[0] == 200.0
    assert st.sum[0] == 2000000.0
    assert st.var[0] == 0.0


def test_with_mask():
    """Stat with mask only counts masked pixels — from upstream sanity."""
    im = Image.new("L", (10, 10), 100)
    mask = Image.new("L", (10, 10), 0)
    mask.putpixel((5, 5), 255)

    st = ImageStat.Stat(im, mask)
    assert st.count[0] == 1
    assert st.mean[0] == 100.0


if __name__ == "__main__":
    pytest.main()
