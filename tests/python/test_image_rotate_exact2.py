"""Additional tests for Image.rotate() — more exact pixel verification."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Rotate 180° exact pixel positions
# ---------------------------------------------------------------------------

def test_rotate_180_top_left_to_bottom_right():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 100)
    out = im.rotate(180)
    assert out.getpixel((9, 9)) == 100


def test_rotate_180_center_unchanged():
    """In a uniform image, center stays same after 180°."""
    im = Image.new("L", (11, 11), 128)
    out = im.rotate(180)
    assert out.getpixel((5, 5)) == 128


def test_rotate_180_non_square():
    im = Image.new("L", (10, 6), 0)
    im.putpixel((0, 0), 200)  # top-left
    out = im.rotate(180)
    # (0, 0) → (9, 5) in 10×6 image
    assert out.getpixel((9, 5)) == 200


# ---------------------------------------------------------------------------
# Rotate 90° CCW (positive angle in Pillow)
# ---------------------------------------------------------------------------

def test_rotate_90ccw_top_right_to_top_left():
    """rotate(90) CCW: (W-1, 0) → (0, 0) in a square image."""
    im = Image.new("L", (10, 10), 0)
    im.putpixel((9, 0), 100)  # top-right
    out = im.rotate(90)
    # After 90° CCW on WxH: (x, y) → (y, W-1-x)
    # (9, 0) → (0, 0) in 10×10
    assert out.getpixel((0, 0)) == 100


def test_rotate_90ccw_top_left_to_bottom_left():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 100)  # top-left
    out = im.rotate(90)
    # (0, 0) → (0, 9) after 90° CCW
    assert out.getpixel((0, 9)) == 100


# ---------------------------------------------------------------------------
# Rotate 90° CW (negative angle)
# ---------------------------------------------------------------------------

def test_rotate_90cw_top_left_to_top_right():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 100)  # top-left
    out = im.rotate(-90)
    # After 90° CW on WxH: (x, y) → (H-1-y, x)
    # (0, 0) → (9, 0) in 10×10
    assert out.getpixel((9, 0)) == 100


# ---------------------------------------------------------------------------
# Rotation of non-square images with expand=True
# ---------------------------------------------------------------------------

def test_rotate_90_expand_wide_image():
    """Rotate wide image 90° CCW with expand: 20×10 → 10×20."""
    im = Image.new("L", (20, 10), 0)
    im.putpixel((0, 0), 100)
    out = im.rotate(90, expand=True)
    assert out.size == (10, 20)


def test_rotate_90_expand_tall_image():
    """Rotate tall image 90° CCW with expand: 10×20 → 20×10."""
    im = Image.new("L", (10, 20), 0)
    im.putpixel((0, 0), 100)
    out = im.rotate(90, expand=True)
    assert out.size == (20, 10)


def test_rotate_90_expand_pixel_value():
    """After expansion, pixel should be at right position."""
    im = Image.new("L", (10, 5), 0)
    im.putpixel((0, 0), 200)
    out = im.rotate(90, expand=True)
    # For 90° CCW with expand: WxH → HxW
    # In a 10×5 image rotated 90° CCW → 5×10
    assert out.size == (5, 10)
    # Pixel at (0,0) in source → (0, 9) in output
    assert out.getpixel((0, 9)) == 200


# ---------------------------------------------------------------------------
# Angle range tests
# ---------------------------------------------------------------------------

def test_rotate_45():
    """Arbitrary angle should work without crashing."""
    im = Image.new("L", (20, 20), 0)
    out = im.rotate(45)
    assert out.size == (20, 20)


def test_rotate_270():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 100)
    out = im.rotate(270)
    assert out.size == (10, 10)
    # 270° CCW = 90° CW: (0,0) → (9, 0)
    assert out.getpixel((9, 0)) == 100


def test_rotate_negative_360():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((3, 4), 200)
    out = im.rotate(-360)
    assert out.getpixel((3, 4)) == 200


def test_rotate_small_angle():
    im = Image.new("L", (20, 20), 128)
    out = im.rotate(1)
    # Small angle: center should still be close to 128
    assert abs(out.getpixel((10, 10)) - 128) <= 5


# ---------------------------------------------------------------------------
# RGB rotation
# ---------------------------------------------------------------------------

def test_rotate_180_rgb():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((0, 0), (100, 150, 200))
    out = im.rotate(180)
    assert out.getpixel((9, 9)) == (100, 150, 200)


def test_rotate_90_rgb():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    out = im.rotate(90)
    assert out.mode == "RGB"
    assert out.size == (10, 10)


if __name__ == "__main__":
    pytest.main()
