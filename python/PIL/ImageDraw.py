"""
PIL.ImageDraw — simple 2-D drawing on Image objects.
"""

import _pil_native
from PIL.ImageColor import getrgb as _getrgb


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


    def polygon(self, xy, fill=None, outline=None, width=1):
        """Draw a polygon.

        *xy* is a sequence of points ``[(x0,y0), (x1,y1), ...]`` or flat ``[x0,y0,x1,y1,...]``.
        """
        coords = _normalise_xy(xy)
        if fill is not None:
            color = fill
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_polygon(
                self._image._handle, list(coords), list(color), True
            )
        if outline is not None:
            color = outline
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_polygon(
                self._image._handle, list(coords), list(color), False
            )
        elif fill is None:
            color = (255, 255, 255)
            _pil_native.draw_polygon(
                self._image._handle, list(coords), list(color), False
            )

    def point(self, xy, fill=None):
        """Draw one or more individual pixels.

        *xy* is a flat list ``[x0, y0, x1, y1, ...]`` or list of tuples
        ``[(x0, y0), (x1, y1), ...]``.
        """
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color,)
        elif isinstance(color, tuple):
            color = list(color)
        coords = _normalise_xy(xy)
        for i in range(0, len(coords), 2):
            x, y = int(coords[i]), int(coords[i + 1])
            _pil_native.image_putpixel(self._image._handle, x, y, list(color))

    def arc(self, xy, start, end, fill=None, width=1):
        """Draw an arc (portion of ellipse outline).

        *xy* is the bounding box ``[(x0,y0),(x1,y1)]`` or ``[x0,y0,x1,y1]``.
        """
        coords = _normalise_box(xy)
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_arc(
            self._image._handle, list(coords), float(start), float(end), list(color)
        )

    def pieslice(self, xy, start, end, fill=None, outline=None, width=1):
        """Draw a pie slice (filled arc with lines to center).

        *xy* is the bounding box.
        """
        coords = _normalise_box(xy)
        color = fill or outline or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        _pil_native.draw_pieslice(
            self._image._handle, list(coords), float(start), float(end),
            list(color), fill is not None
        )

    def chord(self, xy, start, end, fill=None, outline=None, width=1):
        """Draw a chord: arc + straight line closing the endpoints.

        *fill* floods the enclosed region; *outline* draws the boundary.
        """
        coords = _normalise_box(xy)
        if fill is not None:
            color = fill
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_chord(
                self._image._handle, list(coords), float(start), float(end), list(color), True
            )
        if outline is not None:
            color = outline
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_chord(
                self._image._handle, list(coords), float(start), float(end), list(color), False
            )
        if fill is None and outline is None:
            _pil_native.draw_chord(
                self._image._handle, list(coords), float(start), float(end), [255, 255, 255], False
            )

    def text(self, xy, text, fill=None, font=None, anchor=None, **kwargs):
        """Draw text at the given position.

        *xy* is ``(x, y)``.  *fill* is the text colour.
        *font* — a FreeTypeFont (TrueType or bitmap fallback).
        *anchor* — ``"left"`` (default), ``"center"``, or ``"right"``.
        """
        color = fill or (255, 255, 255)
        if isinstance(color, str):
            color = _getrgb(color)
        if isinstance(color, int):
            color = (color, color, color)
        # TrueType path
        if font and hasattr(font, '_handle') and font._handle is not None:
            _pil_native.draw_text_ttf(
                self._image._handle, font._handle,
                float(xy[0]), float(xy[1]), str(text),
                list(color), anchor or "left"
            )
            return
        # Bitmap fallback
        size = 1  # default 8×16
        if font and hasattr(font, 'size'):
            size = 2 if font.size >= 16 else 1
        _pil_native.draw_text(
            self._image._handle, int(xy[0]), int(xy[1]), str(text),
            list(color), size, anchor or "left"
        )


    def textbbox(self, xy, text, font=None, anchor=None, **kwargs):
        """Return bounding box (x0, y0, x1, y1) of text at position *xy*."""
        if font and hasattr(font, '_handle') and font._handle is not None:
            return _pil_native.font_text_bbox(
                font._handle, str(text), float(xy[0]), float(xy[1])
            )
        # Bitmap fallback
        char_w, char_h = 8, 16
        if font and hasattr(font, 'size'):
            scale = 2 if font.size >= 16 else 1
            char_w *= scale
            char_h *= scale
        lines = str(text).split("\n")
        max_len = max(len(line) for line in lines) if lines else 0
        text_w = max_len * char_w
        text_h = len(lines) * char_h

        x, y = int(xy[0]), int(xy[1])
        anc = anchor or "left"
        if anc == "center" or anc == "mm":
            x -= text_w // 2
            y -= text_h // 2
        elif anc == "right" or anc == "rm":
            x -= text_w

        return (x, y, x + text_w, y + text_h)

    def textlength(self, text, font=None, **kwargs):
        """Return width of *text* in pixels."""
        if font and hasattr(font, '_handle') and font._handle is not None:
            return _pil_native.font_text_length(font._handle, str(text))
        char_w = 8
        if font and hasattr(font, 'size'):
            char_w = 16 if font.size >= 16 else 8
        return len(str(text)) * char_w

    def multiline_textbbox(self, xy, text, font=None, spacing=4, **kwargs):
        """Return bounding box of multi-line text."""
        lines = str(text).split("\n")
        if font and hasattr(font, '_handle') and font._handle is not None:
            ascent, descent, _height = _pil_native.font_metrics(font._handle)
            line_h = ascent + descent
            max_w = 0.0
            for line in lines:
                w = _pil_native.font_text_length(font._handle, line)
                if w > max_w:
                    max_w = w
            text_h = len(lines) * line_h + (len(lines) - 1) * spacing if lines else 0
            x, y = float(xy[0]), float(xy[1])
            return (x, y, x + max_w, y + text_h)
        # Bitmap fallback
        char_w, char_h = 8, 16
        if font and hasattr(font, 'size'):
            scale = 2 if font.size >= 16 else 1
            char_w *= scale
            char_h *= scale
        max_len = max(len(line) for line in lines) if lines else 0
        text_w = max_len * char_w
        text_h = len(lines) * char_h + (len(lines) - 1) * spacing if lines else 0
        x, y = int(xy[0]), int(xy[1])
        return (x, y, x + text_w, y + text_h)

    def multiline_text(self, xy, text, fill=None, font=None, anchor=None,
                       spacing=4, align="left", **kwargs):
        """Draw multi-line text, splitting on newlines."""
        color = fill or (255, 255, 255)
        if isinstance(color, int):
            color = (color, color, color)
        if font and hasattr(font, '_handle') and font._handle is not None:
            ascent, descent, _height = _pil_native.font_metrics(font._handle)
            line_h = ascent + descent
        else:
            line_h = 32 if (font and hasattr(font, 'size') and font.size >= 16) else 16

        x, y = float(xy[0]), float(xy[1])
        for line in str(text).split("\n"):
            self.text((x, y), line, fill=color, font=font, anchor=anchor)
            y += line_h + spacing

    def rounded_rectangle(self, xy, radius=0, fill=None, outline=None, width=1):
        """Draw a rounded rectangle.

        Falls back to a regular rectangle (radius is decorative only in our
        bitmap implementation).
        """
        # For a bitmap implementation, we draw a regular rectangle and then
        # round the corners by drawing arcs. Simplified: just draw the rect.
        self.rectangle(xy, fill=fill, outline=outline, width=width)

    def regular_polygon(self, bounding_circle, n_sides, rotation=0,
                        fill=None, outline=None, width=1):
        """Draw a regular polygon inscribed in *bounding_circle*.

        *bounding_circle* is ``(cx, cy, r)`` or ``((cx, cy), r)``.
        """
        import math
        if len(bounding_circle) == 2:
            (cx, cy), r = bounding_circle
        else:
            cx, cy, r = bounding_circle
        points = []
        for i in range(n_sides):
            angle = math.radians(rotation + i * 360 / n_sides - 90)
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append((int(px), int(py)))
        self.polygon(points, fill=fill, outline=outline, width=width)


def Draw(im):
    """Factory function matching ``PIL.ImageDraw.Draw(im)``."""
    return ImageDraw(im)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalise_box(xy):
    """Flatten ``[(x0,y0),(x1,y1)]`` or ``[x0,y0,x1,y1]`` to flat list, ensuring min/max order."""
    if len(xy) == 2 and hasattr(xy[0], "__len__"):
        flat = [xy[0][0], xy[0][1], xy[1][0], xy[1][1]]
    else:
        flat = list(xy)
    # Normalize so x0 <= x1, y0 <= y1
    if flat[0] > flat[2]:
        flat[0], flat[2] = flat[2], flat[0]
    if flat[1] > flat[3]:
        flat[1], flat[3] = flat[3], flat[1]
    return flat


def _normalise_xy(xy):
    """Flatten sequence of points to flat list of ints."""
    flat = []
    for item in xy:
        if hasattr(item, "__len__"):
            flat.extend(item)
        else:
            flat.append(item)
    return flat
