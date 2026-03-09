"""Tests for PIL.ImageStat."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageStat


def test_stat_mean_L():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert stat.mean == [100.0]

def test_stat_mean_RGB():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    stat = ImageStat.Stat(im)
    assert stat.mean == [10.0, 20.0, 30.0]

def test_stat_count():
    im = Image.new("L", (10, 10), 42)
    stat = ImageStat.Stat(im)
    assert stat.count == [100]

def test_stat_extrema():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 1), 200)
    stat = ImageStat.Stat(im)
    assert stat.extrema == [(50, 200)]

def test_stat_median():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert stat.median == [100]

def test_stat_sum():
    im = Image.new("L", (10, 10), 42)
    stat = ImageStat.Stat(im)
    assert stat.sum == [4200]

def test_stat_stddev_uniform():
    im = Image.new("L", (10, 10), 100)
    stat = ImageStat.Stat(im)
    assert stat.stddev == [0.0]

def test_stat_bands():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    stat = ImageStat.Stat(im)
    assert len(stat.mean) == 3
    assert len(stat.count) == 3
    assert len(stat.extrema) == 3


if __name__ == "__main__":
    pytest.main()
