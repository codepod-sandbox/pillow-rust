"""
Tests adapted from upstream Pillow test_imagepath.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagepath.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import array
import math
import pytest
from PIL import ImagePath


def _approx_equal(a, b, tol=1e-6):
    """Check two values or tuples are approximately equal."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < tol
    return all(abs(x - y) < tol for x, y in zip(a, b))


def test_path():
    """Basic ImagePath.Path operations — from upstream."""
    p = ImagePath.Path(list(range(10)))

    # sequence interface
    assert len(p) == 5
    assert _approx_equal(p[0], (0, 1))
    assert _approx_equal(p[-1], (8, 9))
    pts = list(p[:1])
    assert len(pts) == 1 and _approx_equal(pts[0], (0, 1))
    try:
        p["foo"]
        raise AssertionError("Expected TypeError")
    except TypeError:
        pass
    pts = list(p)
    expected = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
    assert len(pts) == len(expected)
    for got, exp in zip(pts, expected):
        assert _approx_equal(got, exp)

    # tolist
    tl = p.tolist()
    for got, exp in zip(tl, expected):
        assert _approx_equal(got, exp)
    flat = p.tolist(True)
    assert len(flat) == 10
    for i, v in enumerate(flat):
        assert _approx_equal(v, i)

    # getbbox
    bbox = p.getbbox()
    assert _approx_equal(bbox, (0, 1, 8, 9))

    # compact
    assert p.compact(5) == 2
    pts = list(p)
    assert len(pts) == 3
    assert _approx_equal(pts[0], (0, 1))
    assert _approx_equal(pts[1], (4, 5))
    assert _approx_equal(pts[2], (8, 9))

    # transform
    p.transform((1, 0, 1, 0, 1, 1))
    pts = list(p)
    assert _approx_equal(pts[0], (1, 2))
    assert _approx_equal(pts[1], (5, 6))
    assert _approx_equal(pts[2], (9, 10))


def test_path_constructors():
    """Various ways to construct a Path — from upstream."""
    for coords in (
        (0, 1),
        [0, 1],
        (0.0, 1.0),
        [0.0, 1.0],
        ((0, 1),),
        [(0, 1)],
        ((0.0, 1.0),),
        [(0.0, 1.0)],
        array.array("f", [0, 1]),
        ImagePath.Path((0, 1)),
    ):
        p = ImagePath.Path(coords)
        pts = list(p)
        assert len(pts) == 1
        assert _approx_equal(pts[0], (0, 1))


def test_path_odd_number_of_coordinates():
    """Odd number of coordinates raises ValueError — from upstream."""
    for coords in ((0,), [0], (0, 1, 2), [0, 1, 2]):
        try:
            ImagePath.Path(coords)
            raise AssertionError(f"Expected ValueError for {coords}")
        except (ValueError, IndexError):
            pass


def test_getbbox():
    """getbbox returns correct bounding box — from upstream."""
    cases = [
        ([0, 1, 2, 3], (0, 1, 2, 3)),
        ([3, 2, 1, 0], (1, 0, 3, 2)),
    ]
    for coords, expected in cases:
        p = ImagePath.Path(coords)
        bbox = p.getbbox()
        assert _approx_equal(bbox, expected), f"{bbox} != {expected}"


def test_map():
    """map() transforms points in-place — from upstream."""
    p = ImagePath.Path(list(range(6)))
    p.map(lambda x, y: (x * 2, y * 3))
    pts = list(p)
    expected = [(0, 3), (4, 9), (8, 15)]
    assert len(pts) == len(expected)
    for got, exp in zip(pts, expected):
        assert _approx_equal(got, exp)


def test_transform():
    """Affine transform in-place — from upstream."""
    p = ImagePath.Path([0, 1, 2, 3])
    theta = math.pi / 15
    p.transform(
        (math.cos(theta), math.sin(theta), 20, -math.sin(theta), math.cos(theta), 20),
    )
    pts = p.tolist()
    assert _approx_equal(pts[0], (20.20791169081776, 20.978147600733806))
    assert _approx_equal(pts[1], (22.58003027392089, 22.518619420565898))


def test_transform_identity():
    """Identity transform leaves points unchanged — derived from upstream."""
    p = ImagePath.Path([0, 1, 4, 5])
    p.transform((1, 0, 0, 0, 1, 0))
    pts = p.tolist()
    assert _approx_equal(pts[0], (0, 1))
    assert _approx_equal(pts[1], (4, 5))


if __name__ == "__main__":
    pytest.main()
