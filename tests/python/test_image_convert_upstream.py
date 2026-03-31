"""
Tests adapted from upstream Pillow test_image_convert.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_convert.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_sanity():
    """convert() between supported modes — adapted from upstream test_sanity."""
    def convert(im, mode):
        out = im.convert(mode)
        assert out.mode == mode
        assert out.size == im.size

    # Limit to modes we support
    modes = ("L", "LA", "RGB", "RGBA")

    for input_mode in modes:
        im = hopper(input_mode)
        for output_mode in modes:
            convert(im, output_mode)

        # Check 0-size image
        im = Image.new(input_mode, (0, 0))
        for output_mode in modes:
            convert(im, output_mode)


def test_unsupported_conversion():
    """convert() with invalid mode raises ValueError — from upstream."""
    im = hopper()
    try:
        im.convert("INVALID")
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_matrix_wrong_mode():
    """Matrix convert requires RGB input — from upstream."""
    im = hopper("L")
    matrix = (
        0.412453, 0.357580, 0.180423, 0,
        0.212671, 0.715160, 0.072169, 0,
        0.019334, 0.119193, 0.950227, 0,
    )
    assert im.mode == "L"
    try:
        im.convert(mode="L", matrix=matrix)
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass


def test_matrix_identity():
    """Identity matrix convert preserves image — from upstream."""
    im = hopper("RGB")
    identity_matrix = (
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
    )
    assert im.mode == "RGB"
    converted_im = im.convert(mode="RGB", matrix=identity_matrix)
    assert_image_equal(converted_im, im)


def test_l_to_rgb():
    """L → RGB expands to 3-channel image — from upstream."""
    im = hopper("L")
    rgb = im.convert("RGB")
    assert rgb.mode == "RGB"
    assert rgb.size == im.size
    # Each channel of the RGB should equal the L channel
    r, g, b = rgb.split()
    assert_image_equal(r, im)
    assert_image_equal(g, im)
    assert_image_equal(b, im)


def test_rgb_to_l():
    """RGB to L convert returns correct mode/size — from upstream."""
    im = hopper("RGB")
    out = im.convert("L")
    assert out.mode == "L"
    assert out.size == im.size


def test_rgba_to_rgb():
    """RGBA to RGB drops alpha channel — from upstream."""
    im = hopper("RGBA")
    out = im.convert("RGB")
    assert out.mode == "RGB"
    assert out.size == im.size


def test_rgb_to_rgba():
    """RGB to RGBA adds opaque alpha — from upstream."""
    im = hopper("RGB")
    out = im.convert("RGBA")
    assert out.mode == "RGBA"
    assert out.size == im.size
    # Alpha should be fully opaque
    alpha = out.getchannel("A")
    solid = Image.new("L", im.size, 255)
    assert_image_equal(alpha, solid)


if __name__ == "__main__":
    pytest.main()
