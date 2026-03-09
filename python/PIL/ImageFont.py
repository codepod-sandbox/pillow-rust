"""
PIL.ImageFont — font handling for ImageDraw.

Supports TrueType fonts via ab_glyph (Rust backend) with an embedded
Liberation Sans Regular as the default font. Falls back to a built-in
8×16 bitmap font when the native backend is unavailable.
"""

try:
    import _pil_native
    _HAS_NATIVE_FONT = True
except ImportError:
    _HAS_NATIVE_FONT = False


class FreeTypeFont:
    """TrueType font object compatible with ImageDraw.text().

    When backed by a native font handle, metrics come from ab_glyph.
    Otherwise falls back to bitmap 8×16 approximation.
    """

    def __init__(self, size=16, _handle=None):
        self.size = size
        self._handle = _handle
        # Bitmap fallback metrics
        self._char_w = 8 * (2 if size >= 16 else 1)
        self._char_h = 16 * (2 if size >= 16 else 1)

    def getbbox(self, text):
        """Return (x0, y0, x1, y1) bounding box for *text*."""
        if self._handle is not None:
            return _pil_native.font_text_bbox(self._handle, str(text), 0.0, 0.0)
        lines = str(text).split("\n")
        max_len = max(len(line) for line in lines) if lines else 0
        w = max_len * self._char_w
        h = len(lines) * self._char_h
        return (0, 0, w, h)

    def getlength(self, text):
        """Return width of *text* in pixels (single line)."""
        if self._handle is not None:
            return _pil_native.font_text_length(self._handle, str(text))
        return len(str(text)) * self._char_w

    def getsize(self, text):
        """Return (width, height) — deprecated, use getbbox instead."""
        bbox = self.getbbox(text)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

    def getmetrics(self):
        """Return (ascent, descent)."""
        if self._handle is not None:
            ascent, descent, _height = _pil_native.font_metrics(self._handle)
            return (int(ascent + 0.5), int(descent + 0.5))
        return (self._char_h, 0)

    def __del__(self):
        if self._handle is not None and _HAS_NATIVE_FONT:
            try:
                _pil_native.font_close(self._handle)
            except Exception:
                pass
            self._handle = None


_default_font = None


def load_default(size=None):
    """Return the default font.

    If *size* is given, returns a font at that pixel size.
    """
    global _default_font
    if size is not None:
        if _HAS_NATIVE_FONT:
            h = _pil_native.font_load_default(float(size))
            return FreeTypeFont(size, _handle=h)
        return FreeTypeFont(size)
    if _default_font is None:
        if _HAS_NATIVE_FONT:
            h = _pil_native.font_load_default(16.0)
            _default_font = FreeTypeFont(16, _handle=h)
        else:
            _default_font = FreeTypeFont(16)
    return _default_font


def truetype(font=None, size=10, index=0, encoding="", layout_engine=None):
    """Load a TrueType font.

    If *font* is a filename, reads the file and loads it via the native
    backend. If the native backend is unavailable or the file can't be
    read, falls back to the default font at the requested size.
    """
    if _HAS_NATIVE_FONT and font is not None:
        try:
            if hasattr(font, 'read'):
                data = font.read()
            else:
                with open(str(font), "rb") as f:
                    data = f.read()
            h = _pil_native.font_load(list(data), float(size))
            return FreeTypeFont(size, _handle=h)
        except Exception:
            pass
    # Fall back to default font at requested size
    return load_default(size)


def load(filename):
    """Load a font from a BDF/PCF file. Returns default font."""
    return load_default(16)
