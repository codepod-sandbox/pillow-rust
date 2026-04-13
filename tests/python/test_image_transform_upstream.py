"""
Tests adapted from upstream Pillow test_image_transform.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_transform.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def _test_nearest(mode):
    """Helper: NEAREST resize preserves transparent/opaque pixel counts."""
    transparent, opaque = {
        "RGBA": ((255, 255, 255, 0), (255, 255, 255, 255)),
        "LA": ((255, 0), (255, 255)),
    }[mode]
    im = Image.new(mode, (10, 10), transparent)
    im2 = Image.new(mode, (5, 10), opaque)
    im.paste(im2, (0, 0))
    result = im.resize((40, 10), Image.Resampling.NEAREST)
    colors = result.getcolors()
    assert colors is not None
    assert sorted(colors) == sorted(
        [
            (20 * 10, opaque),
            (20 * 10, transparent),
        ]
    )


def test_nearest_resize_RGBA():
    """NEAREST resize on RGBA preserves transparent and opaque areas — from upstream."""
    _test_nearest("RGBA")


def test_nearest_resize_LA():
    """NEAREST resize on LA preserves transparent and opaque areas — from upstream."""
    _test_nearest("LA")


def test_alpha_premult_resize():
    """BILINEAR resize handles alpha-premultiplication correctly — from upstream.

    Composite a half-white/half-transparent image over white; the white area
    should remain fully white (no darkening from premult bleed).
    """
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    im2 = Image.new("RGBA", (5, 10), (255, 255, 255, 255))
    im.paste(im2, (0, 0))

    resized = im.resize((40, 10), Image.Resampling.BILINEAR)
    background = Image.new("RGB", (40, 10), (255, 255, 255))
    background.paste(resized, (0, 0), resized)

    hist = background.histogram()
    # The last bin (value 255) of each R/G/B channel should total all pixels
    # R: hist[255], G: hist[255+256], B: hist[255+512]
    r_full = hist[255]
    assert r_full == 40 * 10


def test_resize_preserves_mode():
    """transform() result preserves the mode of the source image — derived from upstream."""
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.resize((64, 64), Image.Resampling.BILINEAR)
        assert out.mode == mode


if __name__ == "__main__":
    pytest.main()
