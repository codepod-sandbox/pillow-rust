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


    def polygon(self, xy, fill=None, outline=None):
        """Draw a filled polygon using scanline fill."""
        pts = _normalise_polygon(xy)
        if len(pts) < 3:
            return

        if fill is not None:
            fill_color = fill if not isinstance(fill, int) else (fill, fill, fill)
            ys = [p[1] for p in pts]
            y_min, y_max = int(min(ys)), int(max(ys))
            n = len(pts)
            for y in range(y_min, y_max + 1):
                intersections = []
                for i in range(n):
                    x0, y0 = pts[i]
                    x1, y1 = pts[(i + 1) % n]
                    if y0 == y1:
                        continue
                    if min(y0, y1) <= y <= max(y0, y1):
                        x = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
                        intersections.append(x)
                intersections.sort()
                # Deduplicate intersections at shared vertices
                deduped = []
                prev = None
                for xi in intersections:
                    if prev is None or abs(xi - prev) > 0.5:
                        deduped.append(xi)
                    prev = xi
                intersections = deduped
                for k in range(0, len(intersections) - 1, 2):
                    x_start = int(intersections[k])
                    x_end = int(intersections[k + 1])
                    if x_start <= x_end:
                        self.line([(x_start, y), (x_end, y)], fill=fill_color, width=1)

        if outline is not None:
            out_color = outline if not isinstance(outline, int) else (outline, outline, outline)
            for i in range(len(pts)):
                self.line([pts[i], pts[(i + 1) % len(pts)]], fill=out_color, width=1)

    def pieslice(self, xy, start, end, fill=None, outline=None):
        """Draw a pie slice (filled wedge) using polygon()."""
        import math
        x0, y0, x1, y1 = _normalise_box_tuple(xy)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        sweep = end - start
        color = fill if fill is not None else (outline if outline is not None else (255, 255, 255))
        if isinstance(color, int):
            color = (color, color, color)
        n_segments = max(16, int(abs(sweep) / 2))
        pts = [(int(cx), int(cy))]
        for i in range(n_segments + 1):
            angle_deg = start + sweep * i / n_segments
            angle_rad = math.radians(angle_deg)
            px = cx + rx * math.cos(angle_rad)
            py = cy + ry * math.sin(angle_rad)
            pts.append((int(px), int(py)))
        self.polygon(pts, fill=color)

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


def _normalise_polygon(xy):
    """Convert sequence of points to list of (x, y) int tuples."""
    pts = []
    for item in xy:
        if hasattr(item, '__len__') and len(item) == 2:
            pts.append((int(item[0]), int(item[1])))
        else:
            raise ValueError(f"Expected (x, y) pairs, got {item!r}")
    return pts


def _normalise_box_tuple(xy):
    """Convert bounding box to (x0, y0, x1, y1) tuple."""
    if hasattr(xy, '__len__') and len(xy) == 4:
        return tuple(int(v) for v in xy)
    if hasattr(xy, '__len__') and len(xy) == 2:
        (x0, y0), (x1, y1) = xy
        return int(x0), int(y0), int(x1), int(y1)
    raise ValueError(f"Expected bounding box, got {xy!r}")


def _normalise_xy(xy):
    """Flatten sequence of points to flat list of ints."""
    flat = []
    for item in xy:
        if hasattr(item, "__len__"):
            flat.extend(item)
        else:
            flat.append(item)
    return flat
