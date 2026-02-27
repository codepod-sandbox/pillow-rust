"""Shared fixtures and helpers for PIL tests."""

import pytest
from PIL import Image


@pytest.fixture
def hopper():
    """Create a deterministic 128x128 test image factory."""
    def _hopper(mode="RGB"):
        if mode in ("RGB", "RGBA", "L", "LA"):
            im = Image.new("RGB", (128, 128))
            for y in range(128):
                for x in range(128):
                    r = (x * 2) % 256
                    g = (y * 2) % 256
                    b = ((x + y) * 3) % 256
                    im.putpixel((x, y), (r, g, b))
            if mode != "RGB":
                im = im.convert(mode)
            return im
        return Image.new(mode, (128, 128))
    return _hopper


def assert_image(im, mode, size):
    assert im.mode == mode, f"expected mode {mode}, got {im.mode}"
    assert im.size == size, f"expected size {size}, got {im.size}"


def assert_image_equal(a, b):
    assert a.mode == b.mode, f"mode mismatch: {a.mode} vs {b.mode}"
    assert a.size == b.size, f"size mismatch: {a.size} vs {b.size}"
    assert a.tobytes() == b.tobytes(), "pixel data differs"
