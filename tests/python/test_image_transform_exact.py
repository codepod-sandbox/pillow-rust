"""Tests for Image.transform() — affine and perspective exact values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# AFFINE transform — identity
# ---------------------------------------------------------------------------

def test_affine_identity():
    """Identity transform should leave the image unchanged."""
    im = Image.new("L", (20, 20), 0)
    im.putpixel((5, 7), 200)
    # Identity: (1, 0, 0, 0, 1, 0)
    out = im.transform((20, 20), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.getpixel((5, 7)) == 200


def test_affine_returns_correct_size():
    im = Image.new("L", (20, 20), 0)
    out = im.transform((30, 40), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.size == (30, 40)


def test_affine_preserves_mode():
    im = Image.new("L", (20, 20), 128)
    out = im.transform((20, 20), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.mode == "L"


def test_affine_preserves_mode_RGB():
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    out = im.transform((20, 20), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.mode == "RGB"


def test_affine_translation():
    """Translate by (5, 5): pixel at (0,0) should appear at (-5,-5) i.e., off-screen."""
    im = Image.new("L", (20, 20), 0)
    im.putpixel((0, 0), 200)
    # Affine data is the inverse transform: (a, b, c, d, e, f) where
    # src_x = a*dst_x + b*dst_y + c
    # src_y = d*dst_x + e*dst_y + f
    # To translate output by (5, 5): src = dst - (5, 5) → c=-5, f=-5
    out = im.transform((20, 20), Image.AFFINE, (1, 0, -5, 0, 1, -5))
    # Original pixel at (0,0) maps to output (5, 5)
    assert out.getpixel((5, 5)) == 200


def test_affine_returns_new_image():
    im = Image.new("L", (20, 20), 0)
    out = im.transform((20, 20), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out is not im


def test_affine_does_not_modify_original():
    im = Image.new("L", (20, 20), 0)
    im.putpixel((5, 5), 200)
    im.transform((20, 20), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert im.getpixel((5, 5)) == 200


# ---------------------------------------------------------------------------
# AFFINE transform — scale
# ---------------------------------------------------------------------------

def test_affine_scale_2x():
    """Scale by 2x (zoom in): pixel at source (0,0) → output (0,0)."""
    im = Image.new("L", (20, 20), 0)
    im.putpixel((0, 0), 200)
    # src = 0.5 * dst → c=0, f=0, a=0.5, e=0.5
    out = im.transform((20, 20), Image.AFFINE, (0.5, 0, 0, 0, 0.5, 0))
    assert out.getpixel((0, 0)) == 200


def test_affine_uniform_image_unchanged():
    """Any affine transform on uniform image stays uniform."""
    im = Image.new("L", (20, 20), 128)
    out = im.transform((20, 20), Image.AFFINE, (1, 0, 2, 0, 1, 3))
    # Interior of uniform image should stay 128
    assert out.getpixel((10, 10)) == 128


# ---------------------------------------------------------------------------
# PERSPECTIVE transform
# ---------------------------------------------------------------------------

def test_perspective_returns_correct_size():
    im = Image.new("L", (20, 20), 0)
    out = im.transform((20, 20), Image.PERSPECTIVE, (1, 0, 0, 0, 1, 0, 0, 0))
    assert out.size == (20, 20)


def test_perspective_preserves_mode():
    im = Image.new("L", (20, 20), 128)
    out = im.transform((20, 20), Image.PERSPECTIVE, (1, 0, 0, 0, 1, 0, 0, 0))
    assert out.mode == "L"


def test_perspective_identity():
    """Identity perspective should approximately preserve the image."""
    im = Image.new("L", (20, 20), 0)
    im.putpixel((10, 10), 200)
    # Identity perspective: (1, 0, 0, 0, 1, 0, 0, 0)
    out = im.transform((20, 20), Image.PERSPECTIVE, (1, 0, 0, 0, 1, 0, 0, 0))
    assert out.getpixel((10, 10)) == 200


# ---------------------------------------------------------------------------
# EXTENT transform — not yet implemented, skip
# ---------------------------------------------------------------------------

def test_extent_crop_region():
    """EXTENT extracts a sub-region and scales to output size."""
    if not hasattr(Image, 'EXTENT'):
        pytest.skip("EXTENT not yet supported")
    im = Image.new("L", (20, 20), 0)
    im.putpixel((5, 5), 200)
    out = im.transform((20, 20), Image.EXTENT, (0, 0, 10, 10))
    assert out.size == (20, 20)


def test_extent_preserves_mode():
    if not hasattr(Image, 'EXTENT'):
        pytest.skip("EXTENT not yet supported")
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    out = im.transform((20, 20), Image.EXTENT, (0, 0, 20, 20))
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# fillcolor parameter
# ---------------------------------------------------------------------------

def test_affine_fillcolor():
    """Pixels that map outside the source should use fillcolor."""
    im = Image.new("L", (10, 10), 128)
    # Translate so entire image is off-screen
    out = im.transform((10, 10), Image.AFFINE, (1, 0, 100, 0, 1, 100), fillcolor=0)
    # Output should be mostly fillcolor
    assert out.getpixel((5, 5)) == 0


def test_affine_fillcolor_default_zero():
    """Default fillcolor is 0."""
    im = Image.new("L", (10, 10), 128)
    # Translate so entire image is off-screen
    out = im.transform((10, 10), Image.AFFINE, (1, 0, 100, 0, 1, 100))
    assert out.getpixel((5, 5)) == 0


if __name__ == "__main__":
    pytest.main()
