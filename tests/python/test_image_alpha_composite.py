"""Tests for Image.alpha_composite() — alpha blending."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic alpha_composite
# ---------------------------------------------------------------------------

def test_alpha_composite_fully_opaque():
    """Fully opaque source replaces destination entirely."""
    dst = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    dst.alpha_composite(src)
    r, g, b, a = dst.getpixel((0, 0))
    assert r == 255
    assert g == 0
    assert b == 0
    assert a == 255


def test_alpha_composite_fully_transparent():
    """Fully transparent source leaves destination unchanged."""
    dst = Image.new("RGBA", (5, 5), (100, 150, 200, 255))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 0))
    dst.alpha_composite(src)
    r, g, b, a = dst.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 255


def test_alpha_composite_half_transparent():
    """Half-transparent source blends with destination."""
    dst = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    src = Image.new("RGBA", (5, 5), (200, 200, 200, 128))
    dst.alpha_composite(src)
    r, g, b, a = dst.getpixel((0, 0))
    # Result should be between 0 and 200
    assert 0 < r < 210
    assert 0 < g < 210
    assert 0 < b < 210
    assert a == 255  # opaque background stays opaque


def test_alpha_composite_returns_none():
    """alpha_composite modifies in-place and returns None."""
    dst = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    result = dst.alpha_composite(src)
    assert result is None


def test_alpha_composite_modifies_dst():
    dst = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    dst.alpha_composite(src)
    # dst should be modified
    r, g, b, a = dst.getpixel((0, 0))
    assert r == 255


# ---------------------------------------------------------------------------
# alpha_composite with dest parameter
# ---------------------------------------------------------------------------

def test_alpha_composite_with_dest_offset():
    """Compositing with offset should only affect the specified region."""
    dst = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
    src = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    dst.alpha_composite(src, dest=(3, 3))
    # Inside composited area
    assert dst.getpixel((3, 3))[0] == 255
    # Outside composited area
    assert dst.getpixel((0, 0))[0] == 0
    assert dst.getpixel((9, 9))[0] == 0


# ---------------------------------------------------------------------------
# Compositing over transparent background
# ---------------------------------------------------------------------------

def test_alpha_composite_over_transparent():
    """Source over transparent background → source color."""
    dst = Image.new("RGBA", (5, 5), (0, 0, 0, 0))  # transparent
    src = Image.new("RGBA", (5, 5), (100, 150, 200, 255))
    dst.alpha_composite(src)
    r, g, b, a = dst.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 255


# ---------------------------------------------------------------------------
# Size preserved
# ---------------------------------------------------------------------------

def test_alpha_composite_size_preserved():
    dst = Image.new("RGBA", (20, 30), (0, 0, 0, 255))
    src = Image.new("RGBA", (20, 30), (255, 0, 0, 255))
    dst.alpha_composite(src)
    assert dst.size == (20, 30)


if __name__ == "__main__":
    pytest.main()
