"""
Additional tests adapted from upstream Pillow test_imagedraw.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagedraw.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageDraw
from helper import assert_image_equal

GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

W, H = 100, 100


def test_ellipse_symmetric():
    """Filled ellipse is symmetric under horizontal flip — from upstream."""
    for width, bbox in (
        (100, (24, 24, 75, 75)),
        (101, (25, 25, 75, 75)),
    ):
        im = Image.new("RGB", (width, 100))
        draw = ImageDraw.Draw(im)
        draw.ellipse(bbox, fill=GREEN, outline=BLUE)
        assert_image_equal(im, im.transpose(Image.Transpose.FLIP_LEFT_RIGHT))


def test_pieslice_no_spikes():
    """Pieslice draws no pixels inside the erased center — from upstream."""
    im = Image.new("RGB", (161, 161), WHITE)
    draw = ImageDraw.Draw(im)
    cxs = (
        [140] * 3
        + list(range(140, 19, -20))
        + [20] * 5
        + list(range(20, 141, 20))
        + [140] * 2
    )
    cys = (
        list(range(80, 141, 20))
        + [140] * 5
        + list(range(140, 19, -20))
        + [20] * 5
        + list(range(20, 80, 20))
    )

    for cx, cy, angle in zip(cxs, cys, range(0, 360, 15)):
        draw.pieslice(
            [cx - 100, cy - 100, cx + 100, cy + 100], angle, angle + 1, fill=BLACK
        )
        draw.point([cx, cy], fill=RED)

    im_pre_erase = im.copy()
    draw.rectangle([21, 21, 139, 139], fill=WHITE)

    assert_image_equal(im, im_pre_erase)


def test_incorrectly_ordered_xy1():
    """Reversed x-coordinates raise ValueError — from upstream."""
    xy = (1, 1, 0, 1)
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    try:
        draw.arc(xy, 10, 260)
        raise AssertionError("Expected ValueError for arc")
    except ValueError:
        pass
    try:
        draw.chord(xy, 10, 260)
        raise AssertionError("Expected ValueError for chord")
    except ValueError:
        pass
    try:
        draw.ellipse(xy)
        raise AssertionError("Expected ValueError for ellipse")
    except ValueError:
        pass
    try:
        draw.pieslice(xy, 10, 260)
        raise AssertionError("Expected ValueError for pieslice")
    except ValueError:
        pass
    try:
        draw.rectangle(xy)
        raise AssertionError("Expected ValueError for rectangle")
    except ValueError:
        pass


def test_incorrectly_ordered_xy2():
    """Reversed y-coordinates raise ValueError — from upstream."""
    xy = (1, 1, 1, 0)
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    try:
        draw.arc(xy, 10, 260)
        raise AssertionError("Expected ValueError for arc")
    except ValueError:
        pass
    try:
        draw.chord(xy, 10, 260)
        raise AssertionError("Expected ValueError for chord")
    except ValueError:
        pass
    try:
        draw.ellipse(xy)
        raise AssertionError("Expected ValueError for ellipse")
    except ValueError:
        pass
    try:
        draw.pieslice(xy, 10, 260)
        raise AssertionError("Expected ValueError for pieslice")
    except ValueError:
        pass
    try:
        draw.rectangle(xy)
        raise AssertionError("Expected ValueError for rectangle")
    except ValueError:
        pass


if __name__ == "__main__":
    pytest.main()
