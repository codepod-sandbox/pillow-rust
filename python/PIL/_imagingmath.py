"""
Python implementation of _imagingmath module.

Provides pixel-level math operations on Image.Image objects.
Operations are named {opname}_{mode} and passed to binop/unop.

Note: ImageMath.py in our PIL directory passes Image.Image objects
(not ptr capsules) to binop/unop, since we control both sides.
"""
from __future__ import annotations

import struct


# ---------------------------------------------------------------------------
# Opcode objects — identify the operation to binop/unop
# ---------------------------------------------------------------------------

class _Op:
    def __init__(self, name: str, mode: str) -> None:
        self.name = name
        self.mode = mode

    def __repr__(self) -> str:
        return f"<_Op {self.name}_{self.mode}>"


# Factory: getattr(_imagingmath, f"{op}_{mode}") returns an _Op
def __getattr__(name: str) -> _Op:
    # name is like "sub_I", "abs_F", "add_L", etc.
    parts = name.rsplit("_", 1)
    if len(parts) == 2:
        opname, mode = parts
        if opname in (
            "add", "sub", "mul", "div", "mod", "pow",
            "and", "or", "xor",
            "abs", "neg", "pos",
            "lt", "le", "eq", "ne", "ge", "gt",
            "lshift", "rshift",
            "min", "max",
        ) and mode in ("L", "I", "F", "1", "RGB", "RGBA"):
            return _Op(opname, mode)
    raise AttributeError(f"module '_imagingmath' has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Pixel iteration helpers — work on Image.Image objects
# ---------------------------------------------------------------------------

def _iter_I(im) -> list[int]:
    """Get all pixel values from an 'I' mode Image as list of ints."""
    data = im.im.tobytes()
    w, h = im.size
    count = w * h
    return [struct.unpack_from('<H', data, i * 2)[0] for i in range(count)]


def _put_I(im, values: list[int]) -> None:
    """Put signed int pixel values back into an 'I' mode Image."""
    buf = bytearray(len(values) * 2)
    for i, v in enumerate(values):
        # Store as u16; negative values wrap (for sub results before abs)
        v_u16 = v & 0xFFFF
        struct.pack_into('<H', buf, i * 2, v_u16)
    im.im.frombytes(bytes(buf))


def _iter_L(im) -> list[int]:
    """Get all pixel values from an 'L' mode Image."""
    data = im.im.tobytes()
    return list(data)


def _put_L(im, values: list[int]) -> None:
    """Put u8 pixel values back into an 'L' mode Image."""
    buf = bytes([max(0, min(255, int(v))) for v in values])
    im.im.frombytes(buf)


def _apply_binop(opname: str, mode: str, out_im, im1, im2) -> None:
    """Apply binary operation pixel-wise. All args are Image.Image objects."""
    if mode in ("I", "F"):
        a = _iter_I(im1)
        b = _iter_I(im2)
        if opname == "add":
            result = [x + y for x, y in zip(a, b)]
        elif opname == "sub":
            # Store as signed-equivalent u16 (wrap on underflow)
            result = [(x - y) & 0xFFFF for x, y in zip(a, b)]
        elif opname == "mul":
            result = [x * y for x, y in zip(a, b)]
        elif opname == "div":
            result = [x // y if y != 0 else 0 for x, y in zip(a, b)]
        elif opname == "mod":
            result = [x % y if y != 0 else 0 for x, y in zip(a, b)]
        elif opname == "min":
            result = [min(x, y) for x, y in zip(a, b)]
        elif opname == "max":
            result = [max(x, y) for x, y in zip(a, b)]
        elif opname == "and":
            result = [x & y for x, y in zip(a, b)]
        elif opname == "or":
            result = [x | y for x, y in zip(a, b)]
        elif opname == "xor":
            result = [x ^ y for x, y in zip(a, b)]
        # Pillow's I/F-mode comparison ops yield 1 for true / 0 for false
        # (not 255 like L-mode), since the result is still in I/F space.
        elif opname == "lt":
            result = [1 if _signed16(x) < _signed16(y) else 0 for x, y in zip(a, b)]
        elif opname == "le":
            result = [1 if _signed16(x) <= _signed16(y) else 0 for x, y in zip(a, b)]
        elif opname == "eq":
            result = [1 if x == y else 0 for x, y in zip(a, b)]
        elif opname == "ne":
            result = [1 if x != y else 0 for x, y in zip(a, b)]
        elif opname == "ge":
            result = [1 if _signed16(x) >= _signed16(y) else 0 for x, y in zip(a, b)]
        elif opname == "gt":
            result = [1 if _signed16(x) > _signed16(y) else 0 for x, y in zip(a, b)]
        else:
            raise NotImplementedError(f"binop {opname}_{mode} not implemented")
        _put_I(out_im, result)
    elif mode == "L":
        a = _iter_L(im1)
        b = _iter_L(im2)
        if opname == "add":
            result = [min(255, x + y) for x, y in zip(a, b)]
        elif opname == "sub":
            result = [max(0, x - y) for x, y in zip(a, b)]
        elif opname == "mul":
            result = [min(255, x * y // 255) for x, y in zip(a, b)]
        elif opname == "min":
            result = [min(x, y) for x, y in zip(a, b)]
        elif opname == "max":
            result = [max(x, y) for x, y in zip(a, b)]
        else:
            raise NotImplementedError(f"binop {opname}_{mode} not implemented")
        _put_L(out_im, result)
    else:
        raise NotImplementedError(f"binop mode {mode} not implemented")


def _signed16(v: int) -> int:
    """Interpret u16 as signed int16."""
    return v if v < 32768 else v - 65536


def _apply_unop(opname: str, mode: str, out_im, im1) -> None:
    """Apply unary operation pixel-wise. out_im, im1 are Image.Image objects."""
    if mode in ("I", "F"):
        a = _iter_I(im1)
        if opname == "abs":
            # Interpret as signed 16-bit, then abs
            result = [abs(_signed16(v)) for v in a]
        elif opname == "neg":
            result = [(-_signed16(v)) & 0xFFFF for v in a]
        elif opname == "pos":
            result = a[:]
        else:
            raise NotImplementedError(f"unop {opname}_{mode} not implemented")
        _put_I(out_im, result)
    elif mode == "L":
        a = _iter_L(im1)
        if opname == "abs":
            result = a[:]
        elif opname == "neg":
            result = [255 - v for v in a]
        else:
            raise NotImplementedError(f"unop {opname}_{mode} not implemented")
        _put_L(out_im, result)
    else:
        raise NotImplementedError(f"unop mode {mode} not implemented")


def binop(op: _Op, out_im, im1, im2) -> None:
    """Apply binary operation op to im1, im2, write result to out_im.
    All arguments are Image.Image objects."""
    _apply_binop(op.name, op.mode, out_im, im1, im2)


def unop(op: _Op, out_im, im1) -> None:
    """Apply unary operation op to im1, write result to out_im.
    All arguments are Image.Image objects."""
    _apply_unop(op.name, op.mode, out_im, im1)
