"""
Tests adapted from upstream Pillow test_imagedraw.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imagedraw.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image, ImageDraw
from conftest import assert_image, assert_image_equal

W, H = 100, 100
X0, Y0 = 25, 25
X1, Y1 = 75, 75


# ---------------------------------------------------------------------------
# Rectangle tests
# ---------------------------------------------------------------------------


def test_rectangle_sanity():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(255, 0, 0))


def test_rectangle_fill():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(255, 0, 0))
    assert im.getpixel((50, 50)) == (255, 0, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_rectangle_outline():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], outline=(0, 255, 0))
    assert im.getpixel((X0, Y0)) == (0, 255, 0)
    assert im.getpixel((X1, Y0)) == (0, 255, 0)
    assert im.getpixel((50, 50)) == (0, 0, 0)


def test_rectangle_flat_coords():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([X0, Y0, X1, Y1], fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)


def test_rectangle_list_of_tuples():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(X0, Y0), (X1, Y1)], fill=(128, 128, 128))
    assert im.getpixel((50, 50)) == (128, 128, 128)


def test_big_rectangle():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(-1, -1), (W + 1, H + 1)], fill=(255, 128, 0))
    assert im.getpixel((0, 0)) == (255, 128, 0)
    assert im.getpixel((W - 1, H - 1)) == (255, 128, 0)


# ---------------------------------------------------------------------------
# Line tests
# ---------------------------------------------------------------------------


def test_line_horizontal():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([(10, 10), (90, 10)], fill=(255, 255, 0))
    assert im.getpixel((50, 10)) == (255, 255, 0)
    assert im.getpixel((50, 50)) == (0, 0, 0)


def test_line_vertical():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([(50, 10), (50, 90)], fill=(0, 255, 255))
    assert im.getpixel((50, 50)) == (0, 255, 255)


def test_line_diagonal():
    im = Image.new("RGB", (20, 20))
    draw = ImageDraw.Draw(im)
    draw.line([(0, 0), (19, 19)], fill=(255, 0, 255))
    assert im.getpixel((10, 10)) == (255, 0, 255)


def test_line_flat_coords():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.line([10, 50, 90, 50], fill=(100, 200, 100))
    assert im.getpixel((50, 50)) == (100, 200, 100)


def test_line_width():
    im = Image.new("RGB", (20, 20))
    draw = ImageDraw.Draw(im)
    draw.line([(5, 10), (14, 10)], fill=(255, 0, 0), width=3)
    assert im.getpixel((10, 10)) == (255, 0, 0)
    assert im.getpixel((10, 9)) == (255, 0, 0)


# ---------------------------------------------------------------------------
# Ellipse tests
# ---------------------------------------------------------------------------


def test_ellipse_fill():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(20, 20), (80, 80)], fill=(255, 0, 0))
    assert im.getpixel((50, 50)) == (255, 0, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_ellipse_outline():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(20, 20), (80, 80)], outline=(0, 255, 0))
    assert im.getpixel((50, 50)) == (0, 0, 0)
    assert im.getpixel((50, 20)) == (0, 255, 0)


# ---------------------------------------------------------------------------
# Text tests
# ---------------------------------------------------------------------------


def test_text_basic():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.text((10, 10), "Hi", fill=(255, 255, 0))
    found = False
    for y in range(10, 26):
        for x in range(10, 30):
            if im.getpixel((x, y)) == (255, 255, 0):
                found = True
                break
        if found:
            break
    assert found


def test_text_center_anchor():
    im = Image.new("RGB", (200, 50))
    draw = ImageDraw.Draw(im)
    draw.text((100, 10), "AB", fill=(255, 0, 0), anchor="center")
    found = False
    for x in range(90, 110):
        if im.getpixel((x, 14)) == (255, 0, 0):
            found = True
            break
    assert found


# ---------------------------------------------------------------------------
# Multiple shapes
# ---------------------------------------------------------------------------


def test_multiple_shapes():
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (30, 30)], fill=(255, 0, 0))
    draw.rectangle([(50, 50), (70, 70)], fill=(0, 0, 255))
    assert im.getpixel((20, 20)) == (255, 0, 0)
    assert im.getpixel((60, 60)) == (0, 0, 255)
    assert im.getpixel((40, 40)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# Draw then save
# ---------------------------------------------------------------------------


def test_draw_then_save(tmp_path):
    im = Image.new("RGB", (50, 50), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (40, 40)], fill=(0, 0, 0))
    path = str(tmp_path / "draw.png")
    im.save(path)
    im2 = Image.open(path)
    assert im2.getpixel((25, 25)) == (0, 0, 0)
    assert im2.getpixel((0, 0)) == (255, 255, 255)


# ---------------------------------------------------------------------------
# Upstream tests — test_imagedraw.py
# ---------------------------------------------------------------------------


def test_ellipse_symmetric():
    """Upstream: a circle ellipse should produce symmetric results.

    Adapted from test_imagedraw.py in Pillow.
    """
    for diameter in (4, 5, 6, 7, 8):
        im = Image.new("RGB", (diameter, diameter))
        draw = ImageDraw.Draw(im)
        draw.ellipse([(0, 0), (diameter - 1, diameter - 1)], fill=(255, 255, 255))
        # Top half must equal flipped bottom half
        top = im.crop((0, 0, diameter, diameter // 2))
        bottom = im.crop((0, diameter - diameter // 2, diameter, diameter))
        flipped = bottom.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        assert top.tobytes() == flipped.tobytes()


def test_incorrectly_ordered_coordinates():
    """Upstream: Draw methods should handle reversed coordinates gracefully.

    Adapted from test_imagedraw.py in Pillow — ensures rectangle with
    swapped corners still draws correctly (or raises a clear error).
    """
    im = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(im)
    # Pillow normalizes reversed coordinates for rectangle
    draw.rectangle([(X1, Y1), (X0, Y0)], fill=(255, 0, 0))
    # Center pixel should be filled regardless of coordinate order
    assert im.getpixel((50, 50)) == (255, 0, 0)


def test_line_zero_length():
    """Upstream: a zero-length line (point) should draw the endpoint pixel."""
    im = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(im)
    draw.line([(5, 5), (5, 5)], fill=(255, 0, 0))
    assert im.getpixel((5, 5)) == (255, 0, 0)


def test_rectangle_L_mode():
    """Upstream: drawing on L mode images."""
    im = Image.new("L", (50, 50))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(10, 10), (40, 40)], fill=200)
    assert im.getpixel((25, 25)) == 200
    assert im.getpixel((0, 0)) == 0


def test_ellipse_L_mode():
    """Upstream: ellipse fill on L mode image."""
    im = Image.new("L", (50, 50))
    draw = ImageDraw.Draw(im)
    draw.ellipse([(10, 10), (40, 40)], fill=128)
    assert im.getpixel((25, 25)) == 128


@pytest.mark.parametrize("mode", ("RGB", "RGBA", "L"))
def test_draw_does_not_change_mode(mode):
    """Upstream: drawing operations must not alter the image mode."""
    im = Image.new(mode, (50, 50))
    draw = ImageDraw.Draw(im)
    fill = (255, 0, 0) if mode in ("RGB", "RGBA") else 200
    draw.rectangle([(5, 5), (45, 45)], fill=fill)
    assert im.mode == mode
