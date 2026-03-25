"""Tests for Image.transform() with EXTENT, AFFINE, and PERSPECTIVE modes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# AFFINE transform
# ---------------------------------------------------------------------------

def test_affine_identity_transform():
    """Identity affine (a=1,b=0,c=0,d=0,e=1,f=0) should give same image."""
    im = Image.new("L", (50, 50), 0)
    im.putpixel((25, 25), 200)
    # Identity: (x, y) -> (x, y)
    out = im.transform((50, 50), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.size == (50, 50)
    assert out.getpixel((25, 25)) == 200


def test_affine_translation():
    """Affine translation (c=dx, f=dy) shifts image."""
    im = Image.new("L", (50, 50), 0)
    im.putpixel((10, 10), 200)
    # Translate: source x = dest_x + 5, source y = dest_y + 5
    out = im.transform((50, 50), Image.AFFINE, (1, 0, 5, 0, 1, 5))
    # Pixel from (10,10) in source should appear at (5,5) in dest
    assert out.getpixel((5, 5)) == 200


def test_affine_output_size():
    im = Image.new("RGB", (100, 100), (0, 0, 0))
    out = im.transform((60, 40), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.size == (60, 40)


def test_affine_preserves_mode():
    im = Image.new("RGB", (50, 50), (100, 150, 200))
    out = im.transform((50, 50), Image.AFFINE, (1, 0, 0, 0, 1, 0))
    assert out.mode == "RGB"


def test_affine_with_fillcolor():
    """Areas outside src after transform should use fillcolor."""
    im = Image.new("L", (50, 50), 100)
    # Large translation — most output will be from outside source
    out = im.transform((50, 50), Image.AFFINE, (1, 0, -40, 0, 1, 0), fillcolor=0)
    # Pixels in top-left that map outside source boundary should be fillcolor
    assert out.getpixel((0, 25)) == 0


# ---------------------------------------------------------------------------
# PERSPECTIVE transform (quad warp)
# ---------------------------------------------------------------------------

def test_perspective_output_size():
    """PERSPECTIVE transform produces specified output size."""
    im = Image.new("L", (100, 100), 128)
    # Identity-ish coefficients
    coeffs = (1, 0, 0, 0, 1, 0, 0, 0)
    out = im.transform((100, 100), Image.PERSPECTIVE, coeffs)
    assert out.size == (100, 100)


def test_perspective_uniform_image():
    """Perspective of a uniform image should be uniform."""
    im = Image.new("L", (100, 100), 150)
    coeffs = (1, 0, 0, 0, 1, 0, 0, 0)
    out = im.transform((100, 100), Image.PERSPECTIVE, coeffs)
    assert out.getpixel((50, 50)) == 150




if __name__ == "__main__":
    pytest.main()
