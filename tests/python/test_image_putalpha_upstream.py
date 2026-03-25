"""Tests for Image.putalpha() and related alpha operations."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# putalpha() with integer value
# ---------------------------------------------------------------------------

def test_putalpha_int_fully_opaque():
    """putalpha(255) makes all pixels fully opaque."""
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 0))
    im.putalpha(255)
    px = im.getpixel((2, 2))
    assert px[3] == 255


def test_putalpha_int_fully_transparent():
    """putalpha(0) makes all pixels fully transparent."""
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 255))
    im.putalpha(0)
    px = im.getpixel((2, 2))
    assert px[3] == 0


def test_putalpha_int_half():
    """putalpha(128) sets alpha to 128."""
    im = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    im.putalpha(128)
    px = im.getpixel((0, 0))
    assert px[0] == 255
    assert px[1] == 0
    assert px[2] == 0
    assert px[3] == 128


def test_putalpha_preserves_rgb():
    """putalpha() should not change RGB channels."""
    im = Image.new("RGBA", (5, 5), (42, 84, 168, 255))
    im.putalpha(50)
    px = im.getpixel((2, 2))
    assert px[0] == 42
    assert px[1] == 84
    assert px[2] == 168
    assert px[3] == 50


def test_putalpha_converts_rgb_to_rgba():
    """putalpha on an RGB image should convert it to RGBA first."""
    im = Image.new("RGB", (5, 5), (100, 200, 50))
    im.putalpha(128)
    assert im.mode == "RGBA"
    px = im.getpixel((2, 2))
    assert px[0] == 100
    assert px[1] == 200
    assert px[2] == 50
    assert px[3] == 128


# ---------------------------------------------------------------------------
# putalpha() with L image
# ---------------------------------------------------------------------------

def test_putalpha_image_uniform():
    """putalpha with a uniform L image sets all alphas."""
    im = Image.new("RGBA", (5, 5), (100, 100, 100, 255))
    alpha = Image.new("L", (5, 5), 100)
    im.putalpha(alpha)
    px = im.getpixel((2, 2))
    assert px[3] == 100


def test_putalpha_image_varying():
    """putalpha with varying L image sets alpha per pixel."""
    im = Image.new("RGBA", (4, 1), (200, 100, 50, 255))
    alpha = Image.new("L", (4, 1), 0)
    alpha.putpixel((0, 0), 0)
    alpha.putpixel((1, 0), 100)
    alpha.putpixel((2, 0), 200)
    alpha.putpixel((3, 0), 255)
    im.putalpha(alpha)
    assert im.getpixel((0, 0))[3] == 0
    assert im.getpixel((1, 0))[3] == 100
    assert im.getpixel((2, 0))[3] == 200
    assert im.getpixel((3, 0))[3] == 255


def test_putalpha_image_preserves_rgb():
    """putalpha via L image should preserve RGB channels."""
    im = Image.new("RGBA", (3, 1), (42, 84, 126, 255))
    alpha = Image.new("L", (3, 1), 50)
    im.putalpha(alpha)
    for x in range(3):
        px = im.getpixel((x, 0))
        assert px[0] == 42
        assert px[1] == 84
        assert px[2] == 126
        assert px[3] == 50


# ---------------------------------------------------------------------------
# alpha_composite (module-level)
# ---------------------------------------------------------------------------

def test_alpha_composite_src_opaque():
    """Fully opaque src completely covers dst."""
    dst = Image.new("RGBA", (5, 5), (100, 100, 100, 255))
    src = Image.new("RGBA", (5, 5), (200, 0, 0, 255))
    out = Image.alpha_composite(dst, src)
    px = out.getpixel((2, 2))
    assert px[0] == 200
    assert px[1] == 0
    assert px[2] == 0
    assert px[3] == 255


def test_alpha_composite_src_transparent():
    """Fully transparent src leaves dst unchanged."""
    dst = Image.new("RGBA", (5, 5), (100, 100, 100, 255))
    src = Image.new("RGBA", (5, 5), (200, 0, 0, 0))
    out = Image.alpha_composite(dst, src)
    px = out.getpixel((2, 2))
    assert px[0] == 100
    assert px[1] == 100
    assert px[2] == 100


def test_alpha_composite_returns_new_image():
    """alpha_composite returns a new RGBA image."""
    dst = Image.new("RGBA", (5, 5), (100, 100, 100, 255))
    src = Image.new("RGBA", (5, 5), (200, 0, 0, 255))
    out = Image.alpha_composite(dst, src)
    assert out.mode == "RGBA"
    assert out is not dst


def test_alpha_composite_requires_same_size():
    """Different sizes should raise ValueError."""
    dst = Image.new("RGBA", (10, 10), 0)
    src = Image.new("RGBA", (5, 5), 0)
    with pytest.raises(ValueError):
        Image.alpha_composite(dst, src)


def test_alpha_composite_requires_rgba():
    """Non-RGBA inputs should raise ValueError."""
    dst = Image.new("RGB", (5, 5), 0)
    src = Image.new("RGBA", (5, 5), 0)
    with pytest.raises(ValueError):
        Image.alpha_composite(dst, src)


# ---------------------------------------------------------------------------
# getchannel() for alpha
# ---------------------------------------------------------------------------

def test_getchannel_A_rgba():
    """getchannel('A') on RGBA returns alpha channel."""
    im = Image.new("RGBA", (5, 5), (255, 0, 0, 128))
    alpha = im.getchannel("A")
    assert alpha.mode == "L"
    assert alpha.getpixel((0, 0)) == 128


def test_getchannel_A_la():
    """getchannel('A') on LA returns alpha channel."""
    im = Image.new("LA", (5, 5), (100, 200))
    alpha = im.getchannel("A")
    assert alpha.mode == "L"
    assert alpha.getpixel((0, 0)) == 200


def test_getchannel_by_index_rgba():
    """getchannel(3) on RGBA returns alpha."""
    im = Image.new("RGBA", (5, 5), (1, 2, 3, 150))
    alpha = im.getchannel(3)
    assert alpha.getpixel((0, 0)) == 150


def test_getchannel_by_index_la():
    """getchannel(1) on LA returns alpha."""
    im = Image.new("LA", (5, 5), (100, 200))
    alpha = im.getchannel(1)
    assert alpha.getpixel((0, 0)) == 200


if __name__ == "__main__":
    pytest.main()
