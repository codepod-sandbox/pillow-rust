"""
Python-level implementation of the 'raw' decoder and encoder.

The upstream Pillow C extension provides these as _imaging.raw_decoder and
_imaging.raw_encoder. We implement them in Python so that PpmImagePlugin
and other plugins that use the 'raw' codec can load images.

We do NOT import from the PIL package at module level to avoid circular
imports (ImageFile imports Image which would cause a cycle).
"""
from __future__ import annotations

import struct
from typing import Any


# ---------------------------------------------------------------------------
# Rawmode helpers
# ---------------------------------------------------------------------------

def _rawmode_bytes_per_pixel(rawmode: str) -> int:
    """Return bytes per pixel for a given rawmode string."""
    _map = {
        "L": 1, "P": 1, "1": 1, "A": 1, "X": 1,
        "LA": 2, "PA": 2,
        "RGB": 3, "BGR": 3, "YCbCr": 3, "LAB": 3, "HSV": 3,
        "RGBA": 4, "BGRA": 4, "RGBX": 4, "RGBa": 4, "CMYK": 4,
        "I": 4, "F": 4,
        "I;16": 2, "I;16B": 2, "I;16L": 2, "I;16N": 2,
        "I;32": 4, "F;32": 4, "F;32B": 4, "F;32BF": 4, "F;32F": 4,
    }
    return _map.get(rawmode, max(1, len(rawmode.rstrip(";LBFNbe0123456789"))))


def _unpack_row(data: bytes, rawmode: str, width: int) -> list:
    """Unpack a row of raw pixel data into a list of pixel values."""
    if rawmode in ("L", "P", "1", "A", "X"):
        return list(data[:width])
    elif rawmode == "LA":
        return [(data[i * 2], data[i * 2 + 1]) for i in range(min(width, len(data) // 2))]
    elif rawmode == "RGB":
        return [(data[i * 3], data[i * 3 + 1], data[i * 3 + 2]) for i in range(min(width, len(data) // 3))]
    elif rawmode == "BGR":
        return [(data[i * 3 + 2], data[i * 3 + 1], data[i * 3]) for i in range(min(width, len(data) // 3))]
    elif rawmode in ("RGBA", "RGBa"):
        return [(data[i * 4], data[i * 4 + 1], data[i * 4 + 2], data[i * 4 + 3]) for i in range(min(width, len(data) // 4))]
    elif rawmode == "BGRA":
        return [(data[i * 4 + 2], data[i * 4 + 1], data[i * 4], data[i * 4 + 3]) for i in range(min(width, len(data) // 4))]
    elif rawmode == "RGBX":
        return [(data[i * 4], data[i * 4 + 1], data[i * 4 + 2]) for i in range(min(width, len(data) // 4))]
    elif rawmode in ("I;16", "I;16L"):
        return [struct.unpack_from("<H", data, i * 2)[0] for i in range(min(width, len(data) // 2))]
    elif rawmode == "I;16B":
        return [struct.unpack_from(">H", data, i * 2)[0] for i in range(min(width, len(data) // 2))]
    elif rawmode == "I;16N":
        return [struct.unpack_from("=H", data, i * 2)[0] for i in range(min(width, len(data) // 2))]
    elif rawmode in ("F;32F",):
        return [struct.unpack_from("<f", data, i * 4)[0] for i in range(min(width, len(data) // 4))]
    elif rawmode in ("F;32BF",):
        return [struct.unpack_from(">f", data, i * 4)[0] for i in range(min(width, len(data) // 4))]
    elif rawmode in ("YCbCr", "LAB", "HSV"):
        return [(data[i * 3], data[i * 3 + 1], data[i * 3 + 2]) for i in range(min(width, len(data) // 3))]
    else:
        bpp = max(1, _rawmode_bytes_per_pixel(rawmode))
        n = min(width, len(data) // bpp)
        return [data[i * bpp] for i in range(n)]


def _pack_pixel(px: Any, rawmode: str, mode: str) -> bytes:
    """Pack a single pixel into raw bytes."""
    if isinstance(px, int):
        px = (px,)
    if rawmode in ("L", "P", "1", "A", "X"):
        v = px[0] if isinstance(px, (tuple, list)) else int(px)
        return bytes([int(v) & 0xFF])
    elif rawmode == "RGB":
        return bytes([int(px[0]) & 0xFF, int(px[1]) & 0xFF, int(px[2]) & 0xFF])
    elif rawmode == "BGR":
        return bytes([int(px[2]) & 0xFF, int(px[1]) & 0xFF, int(px[0]) & 0xFF])
    elif rawmode in ("RGBA", "RGBa"):
        a = int(px[3]) & 0xFF if len(px) >= 4 else 255
        return bytes([int(px[0]) & 0xFF, int(px[1]) & 0xFF, int(px[2]) & 0xFF, a])
    elif rawmode == "BGRA":
        a = int(px[3]) & 0xFF if len(px) >= 4 else 255
        return bytes([int(px[2]) & 0xFF, int(px[1]) & 0xFF, int(px[0]) & 0xFF, a])
    elif rawmode == "LA":
        a = int(px[1]) & 0xFF if len(px) >= 2 else 255
        return bytes([int(px[0]) & 0xFF, a])
    else:
        if isinstance(px, (tuple, list)):
            return bytes([int(v) & 0xFF for v in px])
        return bytes([int(px) & 0xFF])


# ---------------------------------------------------------------------------
# Codec state helper
# ---------------------------------------------------------------------------

class _State:
    """Minimal codec state that tracks image extents."""
    def __init__(self) -> None:
        self.xoff = 0
        self.yoff = 0
        self.xsize = 0
        self.ysize = 0

    def extents(self) -> tuple[int, int, int, int]:
        return (self.xoff, self.yoff,
                self.xoff + self.xsize, self.yoff + self.ysize)


# ---------------------------------------------------------------------------
# RawDecoder
# ---------------------------------------------------------------------------

class RawDecoder:
    """
    Python implementation of the 'raw' decoder.

    Arguments passed via _getdecoder: (rawmode, stride=0, orientation=1)
    """

    _pulls_fd = False

    def __init__(self, mode: str, *args: Any) -> None:
        self.mode = mode
        self.rawmode: str = args[0] if args and args[0] else mode
        self.stride: int = int(args[1]) if len(args) > 1 and args[1] else 0
        self.orientation: int = int(args[2]) if len(args) > 2 and args[2] else 1
        self.im: Any = None
        self.state = _State()
        self.fd: Any = None

    @property
    def pulls_fd(self) -> bool:
        return self._pulls_fd

    def setfd(self, fd: Any) -> None:
        self.fd = fd

    def setimage(self, im: Any, extents: tuple[int, int, int, int] | None = None) -> None:
        self.im = im
        if extents:
            (x0, y0, x1, y1) = extents
        else:
            (x0, y0, x1, y1) = (0, 0, 0, 0)

        if x0 == 0 and x1 == 0:
            w, h = im.size
            self.state.xoff = 0
            self.state.yoff = 0
            self.state.xsize = w
            self.state.ysize = h
        else:
            self.state.xoff = x0
            self.state.yoff = y0
            self.state.xsize = x1 - x0
            self.state.ysize = y1 - y0

    def decode(self, buffer: bytes) -> tuple[int, int]:
        if isinstance(buffer, memoryview):
            buffer = bytes(buffer)
        if not isinstance(buffer, (bytes, bytearray)):
            try:
                buffer = bytes(buffer)
            except Exception:
                return -1, -1

        im = self.im
        if im is None:
            return -1, -2

        (x0, y0, x1, y1) = self.state.extents()
        w = x1 - x0
        h = y1 - y0

        bpp = _rawmode_bytes_per_pixel(self.rawmode)
        row_stride = self.stride if self.stride > 0 else w * bpp

        try:
            if self.orientation == -1:
                src_rows = range(h - 1, -1, -1)
            else:
                src_rows = range(h)

            for dst_row, src_row in enumerate(src_rows):
                offset = src_row * row_stride
                row_data = buffer[offset: offset + w * bpp]
                if len(row_data) < w * bpp:
                    row_data = row_data + b'\x00' * (w * bpp - len(row_data))

                y = y0 + dst_row
                pixels = _unpack_row(row_data, self.rawmode, w)
                for x_off, px in enumerate(pixels):
                    im.putpixel((x0 + x_off, y), px)

        except Exception:
            # If decoding fails, still signal done to avoid hang
            return -1, -3

        return -1, 0  # done, no error

    def cleanup(self) -> None:
        pass


# ---------------------------------------------------------------------------
# RawEncoder
# ---------------------------------------------------------------------------

class RawEncoder:
    """
    Python implementation of the 'raw' encoder.

    Arguments: (rawmode, stride=0, orientation=1)
    """

    def __init__(self, mode: str, *args: Any) -> None:
        self.mode = mode
        self.rawmode: str = args[0] if args and args[0] else mode
        self.stride: int = int(args[1]) if len(args) > 1 and args[1] else 0
        self.orientation: int = int(args[2]) if len(args) > 2 and args[2] else 1
        self.im: Any = None
        self.state = _State()
        self.fd: Any = None

    def setfd(self, fd: Any) -> None:
        self.fd = fd

    def setimage(self, im: Any, extents: tuple[int, int, int, int] | None = None) -> None:
        self.im = im
        if extents:
            (x0, y0, x1, y1) = extents
        else:
            (x0, y0, x1, y1) = (0, 0, 0, 0)

        if x0 == 0 and x1 == 0:
            w, h = im.size
            self.state.xoff = 0
            self.state.yoff = 0
            self.state.xsize = w
            self.state.ysize = h
        else:
            self.state.xoff = x0
            self.state.yoff = y0
            self.state.xsize = x1 - x0
            self.state.ysize = y1 - y0

    def encode(self, bufsize: int) -> tuple[int, int, bytes]:
        """Return raw bytes for the image."""
        im = self.im
        if im is None:
            return 0, -2, b""

        (x0, y0, x1, y1) = self.state.extents()
        w = x1 - x0
        h = y1 - y0

        result = bytearray()
        rows = range(h) if self.orientation == 1 else range(h - 1, -1, -1)
        for row_idx in rows:
            y = y0 + row_idx
            for x_off in range(w):
                px = im.getpixel((x0 + x_off, y))
                result.extend(_pack_pixel(px, self.rawmode, self.mode))

        return len(result), 0, bytes(result)

    def encode_to_pyfd(self) -> tuple[int, int]:
        n, err, data = self.encode(0)
        if self.fd:
            self.fd.write(data)
        return n, err

    def cleanup(self) -> None:
        pass
