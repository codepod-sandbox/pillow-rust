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

    def line(self, xy, fill=None, width=1):
        """Draw a line between points.

        *xy* is ``[(x0, y0), (x1, y1)]`` or ``[x0, y0, x1, y1]``.
        """
        coords = _normalise_xy(xy)
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_line(self._image._handle, list(coords), list(color), width)


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
