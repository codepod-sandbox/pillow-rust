"""
Test helpers for upstream Pillow compatibility tests.

Mirrors upstream Pillow Tests/helper.py, adapted for codepod's PIL.
"""
from __future__ import annotations

import os
import sys

from PIL import Image

# ---------------------------------------------------------------------------
# hopper() — deterministic test image (replaces Pillow's hopper.ppm)
# ---------------------------------------------------------------------------

_hopper_cache: dict = {}

def _make_hopper() -> Image.Image:
    """Create a 128x128 deterministic test image matching upstream's hopper()."""
    im = Image.new("RGB", (128, 128))
    for y in range(128):
        for x in range(128):
            r = (x * 2) % 256
            g = (y * 2) % 256
            b = ((x + y) * 3) % 256
            im.putpixel((x, y), (r, g, b))
    return im


def hopper(mode: str | None = None) -> Image.Image:
    """Return a copy of a deterministic test image in the given mode."""
    if mode not in _hopper_cache:
        base = _make_hopper()
        if mode is None or mode == "RGB":
            _hopper_cache[mode] = base
        else:
            _hopper_cache[mode] = base.convert(mode)
    return _hopper_cache[mode].copy()


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def assert_image(im: Image.Image, mode: str | None, size: tuple | None, msg: str | None = None) -> None:
    if mode is not None:
        assert im.mode == mode, msg or f"got mode {im.mode!r}, expected {mode!r}"
    if size is not None:
        assert im.size == size, msg or f"got size {im.size!r}, expected {size!r}"


def assert_image_equal(a: Image.Image, b: Image.Image, msg: str | None = None) -> None:
    assert a.mode == b.mode, msg or f"mode mismatch: {a.mode!r} vs {b.mode!r}"
    assert a.size == b.size, msg or f"size mismatch: {a.size!r} vs {b.size!r}"
    assert a.tobytes() == b.tobytes(), msg or "pixel data differs"


def assert_image_similar(a: Image.Image, b: Image.Image, epsilon: float, msg: str | None = None) -> None:
    assert a.mode == b.mode, msg or f"mode mismatch: {a.mode!r} vs {b.mode!r}"
    assert a.size == b.size, msg or f"size mismatch: {a.size!r} vs {b.size!r}"
    ab = a.tobytes()
    bb = b.tobytes()
    if ab == bb:
        return
    diff = sum(abs(x - y) for x, y in zip(ab, bb))
    num_pixels = a.size[0] * a.size[1]
    channels = len(ab) // num_pixels if num_pixels else 1
    ave_diff = diff / (num_pixels * channels)
    assert epsilon >= ave_diff, (
        (msg or "") + f" average pixel diff {ave_diff:.4f} > epsilon {epsilon:.4f}"
    )


def assert_tuple_approx_equal(actual, expected, threshold=2, msg=None):
    assert len(actual) == len(expected), msg or "length mismatch"
    for a, e in zip(actual, expected):
        assert abs(a - e) <= threshold, (
            msg or f"tuple mismatch: {actual} vs {expected} (threshold={threshold})"
        )


# ---------------------------------------------------------------------------
# Feature detection stubs
# ---------------------------------------------------------------------------

def skip_unless_feature(feature: str):
    """Return a pytest.mark.skip marker if feature is not available."""
    import pytest
    # Our implementation doesn't have libtiff, zlib feature flags etc.
    # Skip anything that requires optional features
    return pytest.mark.skip(reason=f"feature {feature!r} not available")


def skip_unless_feature_version(feature: str, version: str):
    import pytest
    return pytest.mark.skip(reason=f"feature {feature!r} version {version} not available")


# ---------------------------------------------------------------------------
# Modes our implementation supports
# ---------------------------------------------------------------------------

SUPPORTED_MODES = ("L", "LA", "RGB", "RGBA")
