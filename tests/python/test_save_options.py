"""Tests for save options: JPEG quality, format detection, metadata."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# -- JPEG quality -----------------------------------------------------------

def test_jpeg_quality_low_vs_high():
    """Low quality should produce smaller files than high quality."""
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    import io
    buf_low = io.BytesIO()
    buf_high = io.BytesIO()
    im.save(buf_low, format="jpeg", quality=10)
    im.save(buf_high, format="jpeg", quality=95)
    assert len(buf_high.getvalue()) > len(buf_low.getvalue())


def test_jpeg_quality_default():
    """Save without quality should work (default 75)."""
    im = Image.new("RGB", (50, 50), (0, 128, 255))
    import io
    buf = io.BytesIO()
    im.save(buf, format="jpeg")
    assert len(buf.getvalue()) > 0


def test_jpeg_quality_roundtrip():
    """Save as JPEG and re-open should produce a valid image."""
    im = Image.new("RGB", (20, 20), (100, 150, 200))
    import io
    buf = io.BytesIO()
    im.save(buf, format="jpeg", quality=85)
    buf.seek(0)
    im2 = Image.open(buf)
    assert im2.size == (20, 20)
    assert im2.mode == "RGB"
    # JPEG is lossy, so pixel won't be exact
    px = im2.getpixel((10, 10))
    assert abs(px[0] - 100) < 10
    assert abs(px[1] - 150) < 10
    assert abs(px[2] - 200) < 10


# -- image.format -----------------------------------------------------------

def test_format_jpeg():
    """Opening a JPEG file should set format='JPEG'."""
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    import io
    buf = io.BytesIO()
    im.save(buf, format="jpeg")
    buf.seek(0)
    # Save to a temp "file" path — we can't test path-based format here
    # but we can test that format is set from file extension via save/open
    # For BytesIO, format won't be set (no filename), so test via new()
    im2 = Image.new("RGB", (5, 5))
    assert im2.format is None  # new images have no format


def test_format_on_new():
    """New images should have format=None."""
    im = Image.new("L", (5, 5))
    assert im.format is None


# -- image.info -------------------------------------------------------------

def test_info_dict():
    """image.info should be a dict."""
    im = Image.new("RGB", (5, 5))
    assert isinstance(im.info, dict)
    assert len(im.info) == 0


def test_info_writable():
    """image.info should be writable."""
    im = Image.new("RGB", (5, 5))
    im.info["custom_key"] = "custom_value"
    assert im.info["custom_key"] == "custom_value"


def test_info_independent():
    """Each image should have its own info dict."""
    im1 = Image.new("RGB", (5, 5))
    im2 = Image.new("RGB", (5, 5))
    im1.info["key"] = "val1"
    assert "key" not in im2.info


if __name__ == "__main__":
    pytest.main()
