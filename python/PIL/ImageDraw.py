"""
PIL.ImageDraw — simple 2-D drawing on Image objects.
"""

import _pil_native


class ImageDraw:
    """Draw context bound to an Image instance."""

    def __init__(self, im):
        self._image = im

    def rectangle(self, xy, fill=None, outline=None, width=1):
        """Draw a rectangle.

        *xy* is either ``[(x0, y0), (x1, y1)]`` or ``[x0, y0, x1, y1]``.
        """
        coords = _normalise_box(xy)
        color = fill or outline or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_rectangle(
            self._image._handle, list(coords), list(color), fill is not None
        )

    def ellipse(self, xy, fill=None, outline=None, width=1):
        """Draw an ellipse.

        *xy* is either ``[(x0, y0), (x1, y1)]`` or ``[x0, y0, x1, y1]``.
        """
        coords = _normalise_box(xy)
        color = fill or outline or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_ellipse(
            self._image._handle, list(coords), list(color), fill is not None
        )

    def line(self, xy, fill=None, width=1):
        """Draw a line between points.

        *xy* is ``[(x0, y0), (x1, y1)]`` or ``[x0, y0, x1, y1]``.
        """
        coords = _normalise_xy(xy)
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_line(self._image._handle, list(coords), list(color), width)


    def text(self, xy, text, fill=None, font=None, anchor=None):
        """Draw text at the given position.

        *xy* is ``(x, y)``.  *fill* is the text colour.
        *font* — if it has a ``size`` attribute >= 16, uses 2× scaling.
        *anchor* — ``"left"`` (default), ``"center"``, or ``"right"``.
        """
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        size = 1  # default 8×16
        if font and hasattr(font, 'size'):
            size = 2 if font.size >= 16 else 1
        _pil_native.draw_text(
            self._image._handle, int(xy[0]), int(xy[1]), str(text),
            list(color), size, anchor or "left"
        )


def Draw(im):
    """Factory function matching ``PIL.ImageDraw.Draw(im)``."""
    return ImageDraw(im)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalise_box(xy):
    """Flatten ``[(x0,y0),(x1,y1)]`` or ``[x0,y0,x1,y1]`` to flat list."""
    if len(xy) == 2 and hasattr(xy[0], "__len__"):
        return [xy[0][0], xy[0][1], xy[1][0], xy[1][1]]
    return list(xy)


def _normalise_xy(xy):
    """Flatten sequence of points to flat list of ints."""
    flat = []
    for item in xy:
        if hasattr(item, "__len__"):
            flat.extend(item)
        else:
            flat.append(item)
    return flat
