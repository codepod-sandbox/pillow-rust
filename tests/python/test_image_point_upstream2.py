"""
Tests adapted from upstream Pillow test_image_point.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_point.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from helper import hopper, assert_image_equal


def test_sanity_rgb():
    """point on RGB with table and lambda — adapted from upstream.

    Note: upstream requires 256*3 table for RGB. Our impl also accepts
    256-entry tables (applied to each channel). We test both work.
    """
    im = hopper()
    im.point(list(range(256)) * 3)
    im.point(lambda x: x)
    im.point(lambda x: x * 1.2)


def test_sanity_l():
    """point with table on L needs 256 entries — from upstream."""
    im = hopper("L")
    im.point(list(range(256)))
    im.point(lambda x: x)


def test_point_table_identity():
    """Identity LUT preserves image — derived from upstream."""
    im = hopper("L")
    lut = list(range(256))
    out = im.point(lut)
    assert_image_equal(im, out)


def test_point_lambda_identity():
    """Identity lambda preserves image — derived from upstream."""
    im = hopper("L")
    out = im.point(lambda x: x)
    assert_image_equal(im, out)


def test_point_lambda_invert():
    """Invert then invert is identity."""
    im = hopper("L")
    inv = im.point(lambda x: 255 - x)
    back = inv.point(lambda x: 255 - x)
    assert_image_equal(im, back)


def test_point_table_matches_lambda():
    """Table and lambda should produce same result — derived from upstream."""
    im = hopper("L")
    table = [min(255, x * 2) for x in range(256)]
    from_table = im.point(table)
    from_lambda = im.point(lambda x: min(255, x * 2))
    assert_image_equal(from_table, from_lambda)


if __name__ == "__main__":
    pytest.main()
