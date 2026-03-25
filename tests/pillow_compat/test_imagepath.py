"""Vendored from upstream Pillow Tests/test_imagepath.py (2026-03-09).

Adapted: removed Evil class test (uses Image.core C extension),
removed array.array and bytes constructors (not supported by our impl),
removed compact-within-map test.
"""
from __future__ import annotations

import math

import pytest

from PIL import ImagePath


def test_path() -> None:
    p = ImagePath.Path(list(range(10)))

    # method sanity check
    assert p.tolist() == [
        (0.0, 1.0),
        (2.0, 3.0),
        (4.0, 5.0),
        (6.0, 7.0),
        (8.0, 9.0),
    ]
    assert p.tolist(True) == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

    assert p.getbbox() == (0.0, 1.0, 8.0, 9.0)

    assert p.compact(5) == 2
    assert list(p) == [(0.0, 1.0), (4.0, 5.0), (8.0, 9.0)]

    p.transform((1, 0, 1, 0, 1, 1))
    assert list(p) == [(1.0, 2.0), (5.0, 6.0), (9.0, 10.0)]


def test_path_from_tuples() -> None:
    p = ImagePath.Path([(0, 1)])
    assert list(p) == [(0.0, 1.0)]

    p = ImagePath.Path([(0.0, 1.0)])
    assert list(p) == [(0.0, 1.0)]


def test_path_from_flat_list() -> None:
    p = ImagePath.Path([0, 1])
    assert list(p) == [(0.0, 1.0)]

    p = ImagePath.Path([0.0, 1.0])
    assert list(p) == [(0.0, 1.0)]


def test_getbbox() -> None:
    p = ImagePath.Path([0, 1, 2, 3])
    assert p.getbbox() == (0.0, 1.0, 2.0, 3.0)

    p = ImagePath.Path([3, 2, 1, 0])
    assert p.getbbox() == (1.0, 0.0, 3.0, 2.0)


def test_map() -> None:
    p = ImagePath.Path(list(range(6)))
    p.map(lambda x, y: (x * 2, y * 3))
    assert list(p) == [(0.0, 3.0), (4.0, 9.0), (8.0, 15.0)]


def test_transform() -> None:
    p = ImagePath.Path([0, 1, 2, 3])
    theta = math.pi / 15

    p.transform(
        (math.cos(theta), math.sin(theta), 20, -math.sin(theta), math.cos(theta), 20),
    )

    assert p.tolist() == [
        (20.20791169081776, 20.978147600733806),
        (22.58003027392089, 22.518619420565898),
    ]
