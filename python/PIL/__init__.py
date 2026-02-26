"""
PIL — Python Imaging Library (codepod WASM implementation)

Backed by the Rust `image` crate via _pil_native.
"""

from PIL.Image import Image, open, new
from PIL.Image import (
    FLIP_LEFT_RIGHT,
    FLIP_TOP_BOTTOM,
    ROTATE_90,
    ROTATE_180,
    ROTATE_270,
    TRANSPOSE,
    TRANSVERSE,
)
