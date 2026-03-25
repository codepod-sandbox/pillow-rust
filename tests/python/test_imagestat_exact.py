"""Tests for ImageStat — exact statistical values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageStat


# ---------------------------------------------------------------------------
# Stat.count
# ---------------------------------------------------------------------------

def test_stat_count_L():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert stat.count == [100]  # 10*10 pixels, 1 band


def test_stat_count_RGB():
    im = Image.new("RGB", (5, 4), (100, 150, 200))
    stat = ImageStat.Stat(im)
    assert stat.count == [20, 20, 20]  # 5*4=20 pixels per band


def test_stat_count_RGBA():
    im = Image.new("RGBA", (3, 3), (100, 150, 200, 255))
    stat = ImageStat.Stat(im)
    assert stat.count == [9, 9, 9, 9]  # 4 bands


# ---------------------------------------------------------------------------
# Stat.sum (sum of pixel values)
# ---------------------------------------------------------------------------

def test_stat_sum_uniform_L():
    im = Image.new("L", (4, 4), 10)  # 16 pixels * 10 = 160
    stat = ImageStat.Stat(im)
    assert stat.sum == [160.0]


def test_stat_sum_zeros():
    im = Image.new("L", (10, 10), 0)
    stat = ImageStat.Stat(im)
    assert stat.sum == [0.0]


def test_stat_sum_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))  # 4 pixels each
    stat = ImageStat.Stat(im)
    assert stat.sum[0] == 40.0   # R: 4 * 10
    assert stat.sum[1] == 80.0   # G: 4 * 20
    assert stat.sum[2] == 120.0  # B: 4 * 30


# ---------------------------------------------------------------------------
# Stat.mean (average pixel value)
# ---------------------------------------------------------------------------

def test_stat_mean_uniform_L():
    im = Image.new("L", (10, 10), 128)
    stat = ImageStat.Stat(im)
    assert abs(stat.mean[0] - 128.0) < 0.01


def test_stat_mean_zero():
    im = Image.new("L", (10, 10), 0)
    stat = ImageStat.Stat(im)
    assert stat.mean[0] == 0.0


def test_stat_mean_mixed():
    """Mean of two pixels: 0 and 200 → 100."""
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 200)
    stat = ImageStat.Stat(im)
    assert abs(stat.mean[0] - 100.0) < 0.01


def test_stat_mean_RGB():
    im = Image.new("RGB", (5, 5), (50, 100, 150))
    stat = ImageStat.Stat(im)
    assert abs(stat.mean[0] - 50.0) < 0.01
    assert abs(stat.mean[1] - 100.0) < 0.01
    assert abs(stat.mean[2] - 150.0) < 0.01


# ---------------------------------------------------------------------------
# Stat.median
# ---------------------------------------------------------------------------

def test_stat_median_uniform():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert stat.median[0] == 100


def test_stat_median_two_values():
    """Median of 0 and 200 depends on implementation — just check range."""
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 200)
    stat = ImageStat.Stat(im)
    # Median should be between 0 and 200
    assert 0 <= stat.median[0] <= 200


# ---------------------------------------------------------------------------
# Stat.extrema (min, max per band)
# ---------------------------------------------------------------------------

def test_stat_extrema_L():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 50)
    im.putpixel((9, 9), 200)
    stat = ImageStat.Stat(im)
    lo, hi = stat.extrema[0]
    assert lo == 0
    assert hi == 200


def test_stat_extrema_uniform():
    im = Image.new("L", (10, 10), 128)
    stat = ImageStat.Stat(im)
    lo, hi = stat.extrema[0]
    assert lo == 128
    assert hi == 128


def test_stat_extrema_RGB():
    im = Image.new("RGB", (3, 3), (50, 100, 150))
    stat = ImageStat.Stat(im)
    assert stat.extrema[0] == (50, 50)
    assert stat.extrema[1] == (100, 100)
    assert stat.extrema[2] == (150, 150)


def test_stat_extrema_full_range():
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 255)
    stat = ImageStat.Stat(im)
    lo, hi = stat.extrema[0]
    assert lo == 0
    assert hi == 255


# ---------------------------------------------------------------------------
# Stat.var and stddev
# ---------------------------------------------------------------------------

def test_stat_var_uniform_zero():
    """Uniform image has zero variance."""
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert abs(stat.var[0]) < 0.01


def test_stat_stddev_uniform_zero():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert abs(stat.stddev[0]) < 0.01


def test_stat_stddev_nonnegative():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 200)
    stat = ImageStat.Stat(im)
    assert stat.stddev[0] >= 0


if __name__ == "__main__":
    pytest.main()
