"""
PIL.Image — core image class and factory functions.
"""

import _pil_native

# ---------------------------------------------------------------------------
# Transpose constants (match Pillow)
# ---------------------------------------------------------------------------

FLIP_LEFT_RIGHT = 0
FLIP_TOP_BOTTOM = 1
ROTATE_90 = 2
ROTATE_180 = 3
ROTATE_270 = 4
TRANSPOSE = 5
TRANSVERSE = 6

# Resampling aliases (Pillow 10.x style)
NEAREST = "nearest"
BILINEAR = "bilinear"
BICUBIC = "bicubic"
LANCZOS = "lanczos"

# ---------------------------------------------------------------------------
# Image class
# ---------------------------------------------------------------------------

class Image:
    """Wraps a native image handle returned by _pil_native."""

    def __init__(self, _handle):
        self._handle = _handle

    # -- properties ---------------------------------------------------------

    @property
    def size(self):
        """Return (width, height) tuple."""
        return _pil_native.image_size(self._handle)

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def mode(self):
        """Return the image mode string (e.g. 'RGB', 'RGBA', 'L')."""
        return _pil_native.image_mode(self._handle)

    # -- pixel access -------------------------------------------------------

    def getpixel(self, xy):
        """Return the pixel value at (x, y)."""
        return _pil_native.image_getpixel(self._handle, xy[0], xy[1])

    def putpixel(self, xy, color):
        """Set the pixel at (x, y) to *color*."""
        if isinstance(color, int):
            color = (color,)
        _pil_native.image_putpixel(self._handle, xy[0], xy[1], list(color))

    # -- transforms ---------------------------------------------------------

    def resize(self, size, resample=None, **_kw):
        """Return a resized copy."""
        if resample is not None:
            return Image(_pil_native.image_resize(self._handle, size[0], size[1], resample))
        return Image(_pil_native.image_resize(self._handle, size[0], size[1]))

    def crop(self, box=None):
        """Return a cropped copy. *box* is (left, upper, right, lower)."""
        if box is None:
            return self.copy()
        return Image(_pil_native.image_crop(self._handle, list(box)))

    def rotate(self, angle, resample=None, expand=False, **_kw):
        """Return a rotated copy (counter-clockwise, in degrees)."""
        return Image(_pil_native.image_rotate(self._handle, float(angle), expand))

    def transpose(self, method):
        """Return a transposed copy (flip / rotate by 90-degree multiples)."""
        return Image(_pil_native.image_transpose(self._handle, method))

    def convert(self, mode, **_kw):
        """Return a copy converted to the given mode ('RGB', 'L', etc.)."""
        return Image(_pil_native.image_convert(self._handle, mode))

    # -- serialisation ------------------------------------------------------

    def save(self, fp, format=None, **_kw):
        """Save the image to *fp* (filename or file-like object)."""
        if format is None and isinstance(fp, str):
            ext = fp.rsplit(".", 1)[-1] if "." in fp else ""
            format = ext.lower() or "png"
        fmt = format or "png"
        data = _pil_native.image_save(self._handle, fmt)
        if isinstance(fp, str):
            with __builtins__["open"](fp, "wb") if isinstance(__builtins__, dict) else __builtins__.open(fp, "wb") as f:
                f.write(data)
        else:
            fp.write(data)

    def tobytes(self):
        """Return raw pixel bytes."""
        return bytes(_pil_native.image_tobytes(self._handle))

    def getdata(self):
        """Return a flat sequence of pixel values."""
        raw = self.tobytes()
        m = self.mode
        bands = {"L": 1, "LA": 2, "RGB": 3, "RGBA": 4}.get(m, 3)
        if bands == 1:
            return list(raw)
        return [tuple(raw[i:i + bands]) for i in range(0, len(raw), bands)]

    # -- copy / close -------------------------------------------------------

    def copy(self):
        """Return an independent copy."""
        return Image(_pil_native.image_copy(self._handle))

    def close(self):
        """Release the underlying native handle."""
        if self._handle is not None:
            _pil_native.image_close(self._handle)
            self._handle = None

    # -- filter -------------------------------------------------------------

    def filter(self, f):
        """Apply *f* (an ImageFilter object) and return a new Image."""
        args = getattr(f, "args", None)
        if args is not None:
            return Image(_pil_native.image_filter(self._handle, f.name, args))
        return Image(_pil_native.image_filter(self._handle, f.name))

    # -- dunder helpers -----------------------------------------------------

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __repr__(self):
        if self._handle is None:
            return "<PIL.Image closed>"
        w, h = self.size
        return f"<PIL.Image mode={self.mode} size={w}x{h}>"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


# ---------------------------------------------------------------------------
# Module-level factory functions
# ---------------------------------------------------------------------------

def open(fp, mode="r"):
    """Open an image file. *fp* can be a filename (str) or a file-like object."""
    if isinstance(fp, str):
        _open = __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
        with _open(fp, "rb") as f:
            data = f.read()
    elif isinstance(fp, (bytes, bytearray)):
        data = bytes(fp)
    else:
        data = fp.read()
    return Image(_pil_native.image_open(data))


def new(mode, size, color=0):
    """Create a new image with the given *mode* and *size*."""
    if isinstance(color, int):
        if mode in ("RGB", "RGBA"):
            color = [color, color, color] + ([255] if mode == "RGBA" else [])
        elif mode == "L":
            color = [color]
        elif mode == "LA":
            color = [color, 255]
        else:
            color = [color]
    elif isinstance(color, tuple):
        color = list(color)
    return Image(_pil_native.image_new(mode, size[0], size[1], color))
