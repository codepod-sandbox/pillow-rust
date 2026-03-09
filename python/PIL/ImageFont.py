"""
PIL.ImageFont — font handling for ImageDraw.

This implementation provides a basic bitmap font. TrueType font loading
is stubbed — ``truetype()`` returns the built-in bitmap font scaled to
approximate the requested size.
"""


class FreeTypeFont:
    """Minimal font object compatible with ImageDraw.text().

    Attributes:
        size: font size in pixels (affects 1× vs 2× rendering)
    """

    def __init__(self, size=16):
        self.size = size
        self._char_w = 8 * (2 if size >= 16 else 1)
        self._char_h = 16 * (2 if size >= 16 else 1)

    def getbbox(self, text):
        """Return (x0, y0, x1, y1) bounding box for *text*."""
        lines = str(text).split("\n")
        max_len = max(len(line) for line in lines) if lines else 0
        w = max_len * self._char_w
        h = len(lines) * self._char_h
        return (0, 0, w, h)

    def getlength(self, text):
        """Return width of *text* in pixels (single line)."""
        return len(str(text)) * self._char_w

    def getsize(self, text):
        """Return (width, height) — deprecated, use getbbox instead."""
        bbox = self.getbbox(text)
        return (bbox[2], bbox[3])

    def getmetrics(self):
        """Return (ascent, descent)."""
        return (self._char_h, 0)


_default_font = None


def load_default(size=None):
    """Return the built-in bitmap font.

    If *size* is given, returns a font scaled to that size.
    """
    global _default_font
    if size is not None:
        return FreeTypeFont(size)
    if _default_font is None:
        _default_font = FreeTypeFont(16)
    return _default_font


def truetype(font=None, size=10, index=0, encoding="", layout_engine=None):
    """Load a TrueType font.

    In this implementation, returns the built-in bitmap font sized to
    approximate *size*. The *font* path is accepted but ignored.
    """
    return FreeTypeFont(size)


def load(filename):
    """Load a font from a BDF/PCF file. Returns default font."""
    return FreeTypeFont(16)
