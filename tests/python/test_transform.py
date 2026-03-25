"""Tests for image.transform(), ImageSequence, and ImagePath."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageSequence, ImagePath


# -- transform (affine) ----------------------------------------------------

def test_affine_identity():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    im.putpixel((5, 5), (0, 255, 0))
    out = im.transform((10, 10), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.getpixel((5, 5)) == (0, 255, 0)


def test_affine_translate():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    im.putpixel((5, 5), (0, 255, 0))
    out = im.transform((10, 10), Image.AFFINE, (1, 0, -3, 0, 1, -2))
    assert out.getpixel((8, 7)) == (0, 255, 0)


def test_affine_scale():
    im = Image.new("L", (20, 20), 0)
    im.putpixel((10, 10), 255)
    out = im.transform((40, 40), Image.AFFINE, (0.5, 0, 0, 0, 0.5, 0))
    assert out.getpixel((20, 20)) == 255


def test_affine_mode_preservation():
    im = Image.new("L", (10, 10), 100)
    out = im.transform((10, 10), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.mode == "L"


def test_affine_resize():
    im = Image.new("RGB", (20, 20), (42, 42, 42))
    out = im.transform((10, 10), Image.AFFINE, (2, 0, 0, 0, 2, 0))
    assert out.size == (10, 10)


# -- transform (perspective) -----------------------------------------------

def test_perspective_identity():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    im.putpixel((5, 5), (0, 255, 0))
    out = im.transform((10, 10), Image.PERSPECTIVE, (1, 0, 0, 0, 1, 0, 0, 0))
    assert out.getpixel((5, 5)) == (0, 255, 0)


def test_perspective_mode():
    im = Image.new("L", (10, 10), 50)
    out = im.transform((10, 10), Image.PERSPECTIVE, (1, 0, 0, 0, 1, 0, 0, 0))
    assert out.mode == "L"


# -- ImageSequence ---------------------------------------------------------

def test_iterator_single_frame():
    im = Image.new("RGB", (5, 5), (1, 2, 3))
    frames = list(ImageSequence.Iterator(im))
    assert len(frames) == 1


def test_all_frames():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    frames = ImageSequence.all_frames(im)
    assert len(frames) == 1
    assert frames[0].getpixel((0, 0)) == (10, 20, 30)


def test_all_frames_with_func():
    im = Image.new("L", (5, 5), 100)
    frames = ImageSequence.all_frames(im, func=lambda f: f.convert("RGB"))
    assert len(frames) == 1
    assert frames[0].mode == "RGB"


# -- ImagePath -------------------------------------------------------------

def test_path_from_tuples():
    p = ImagePath.Path([(0, 0), (10, 0), (10, 10)])
    assert len(p) == 3
    assert p[0] == (0.0, 0.0)


def test_path_from_flat():
    p = ImagePath.Path([0, 0, 5, 5, 10, 10])
    assert len(p) == 3
    assert p[1] == (5.0, 5.0)


def test_path_getbbox():
    p = ImagePath.Path([(0, 0), (10, 0), (10, 10), (0, 10)])
    assert p.getbbox() == (0.0, 0.0, 10.0, 10.0)


def test_path_tolist_flat():
    p = ImagePath.Path([(1, 2), (3, 4)])
    assert p.tolist(flat=1) == [1.0, 2.0, 3.0, 4.0]


def test_path_tolist_tuples():
    p = ImagePath.Path([(1, 2), (3, 4)])
    assert p.tolist() == [(1.0, 2.0), (3.0, 4.0)]


def test_path_transform():
    p = ImagePath.Path([(1, 0), (0, 1)])
    p.transform((2, 0, 0, 0, 2, 0))  # scale 2x
    assert p[0] == (2.0, 0.0)
    assert p[1] == (0.0, 2.0)


def test_path_compact():
    p = ImagePath.Path([(0, 0), (0.5, 0.5), (10, 10)])
    n = p.compact(distance=2)
    assert n == 1  # middle point removed (too close to first)
    assert len(p) == 2


def test_path_empty_bbox():
    p = ImagePath.Path()
    assert p.getbbox() is None


if __name__ == "__main__":
    pytest.main()
