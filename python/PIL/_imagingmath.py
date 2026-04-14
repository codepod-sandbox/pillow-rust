"""
Stub _imagingmath module.

The real _imagingmath is a C extension in upstream Pillow that performs
pixel-level math operations on images. We provide a minimal stub so that
ImageMath can be imported without errors. Operations that actually require
math will still fail at runtime (AttributeError on mode-specific ops).
"""
from __future__ import annotations


def unop(op, out, im1):
    """Apply unary operation op to im1, write result to out."""
    raise NotImplementedError("_imagingmath operations not implemented in pyo3-imaging")


def binop(op, out, im1, im2):
    """Apply binary operation op to im1, im2, write result to out."""
    raise NotImplementedError("_imagingmath operations not implemented in pyo3-imaging")
