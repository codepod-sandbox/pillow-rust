"""Tests for additional Image methods: getchannel, reduce, stubs, eval, gradients."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# -- getchannel -------------------------------------------------------------

def test_getchannel_by_name():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    assert im.getchannel("R").getpixel((0, 0)) == 100
    assert im.getchannel("G").getpixel((0, 0)) == 150
    assert im.getchannel("B").getpixel((0, 0)) == 200


def test_getchannel_by_index():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    assert im.getchannel(0).getpixel((0, 0)) == 10
    assert im.getchannel(1).getpixel((0, 0)) == 20
    assert im.getchannel(2).getpixel((0, 0)) == 30


def test_getchannel_mode():
    im = Image.new("RGBA", (5, 5), (1, 2, 3, 4))
    ch = im.getchannel("A")
    assert ch.mode == "L"
    assert ch.getpixel((0, 0)) == 4


def test_getchannel_l():
    im = Image.new("L", (5, 5), 42)
    ch = im.getchannel("L")
    assert ch.getpixel((0, 0)) == 42


def test_getchannel_invalid():
    im = Image.new("RGB", (5, 5))
    try:
        im.getchannel("X")
        assert False, "should raise ValueError"
    except ValueError:
        pass


# -- reduce -----------------------------------------------------------------

def test_reduce_int():
    im = Image.new("RGB", (100, 80), (42, 42, 42))
    out = im.reduce(2)
    assert out.size == (50, 40)


def test_reduce_tuple():
    im = Image.new("RGB", (100, 80))
    out = im.reduce((4, 2))
    assert out.size == (25, 40)


def test_reduce_with_box():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    out = im.reduce(2, box=(0, 0, 50, 50))
    assert out.size == (25, 25)


# -- stubs ------------------------------------------------------------------

def test_load_noop():
    im = Image.new("L", (5, 5))
    im.load()  # should not raise


def test_show_noop():
    im = Image.new("L", (5, 5))
    im.show()
    im.show(title="test")


def test_tell():
    im = Image.new("L", (5, 5))
    assert im.tell() == 0


def test_seek_zero():
    im = Image.new("L", (5, 5))
    im.seek(0)


def test_seek_nonzero_raises():
    im = Image.new("L", (5, 5))
    try:
        im.seek(1)
        assert False, "should raise EOFError"
    except EOFError:
        pass


def test_n_frames():
    im = Image.new("L", (5, 5))
    assert im.n_frames == 1


def test_is_animated():
    im = Image.new("L", (5, 5))
    assert im.is_animated == False


# -- Image.eval (PIL API, applies function to pixels) ----------------------

def test_image_eval_invert():
    im = Image.new("L", (5, 5), 100)
    # Image.eval applies a function to each pixel value
    out = Image.eval(im, lambda x: 255 - x)
    assert out.getpixel((2, 2)) == 155


# -- gradients --------------------------------------------------------------

def test_linear_gradient():
    lg = Image.linear_gradient("L")
    assert lg.size == (256, 256)
    assert lg.mode == "L"
    assert lg.getpixel((0, 0)) == 0
    assert lg.getpixel((0, 255)) == 255


def test_radial_gradient():
    rg = Image.radial_gradient("L")
    assert rg.size == (256, 256)
    center = rg.getpixel((128, 128))
    corner = rg.getpixel((0, 0))
    assert center < corner


if __name__ == "__main__":
    pytest.main()
