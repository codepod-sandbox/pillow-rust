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

# ---------------------------------------------------------------------------
# Transpose enum (Pillow 10.x style)
# ---------------------------------------------------------------------------

class Transpose:
    """Enum-like class for transpose operations (matches Pillow 10.x)."""
    FLIP_LEFT_RIGHT = 0
    FLIP_TOP_BOTTOM = 1
    ROTATE_90 = 2
    ROTATE_180 = 3
    ROTATE_270 = 4
    TRANSPOSE = 5
    TRANSVERSE = 6

# ---------------------------------------------------------------------------
# Resampling aliases (Pillow 10.x style)
# ---------------------------------------------------------------------------

NEAREST = "nearest"
BILINEAR = "bilinear"
BICUBIC = "bicubic"
LANCZOS = "lanczos"
BOX = "nearest"       # approximation
HAMMING = "bilinear"  # approximation

class Resampling:
    """Enum-like class for resampling filters (matches Pillow 10.x)."""
    NEAREST = "nearest"
    BOX = "nearest"
    BILINEAR = "bilinear"
    HAMMING = "bilinear"
    BICUBIC = "bicubic"
    LANCZOS = "lanczos"

# ---------------------------------------------------------------------------
# Supported modes
# ---------------------------------------------------------------------------

MODES = ["L", "LA", "RGB", "RGBA"]

# ---------------------------------------------------------------------------
# Band names per mode
# ---------------------------------------------------------------------------

_MODE_BANDS = {
    "L": ("L",),
    "LA": ("L", "A"),
    "RGB": ("R", "G", "B"),
    "RGBA": ("R", "G", "B", "A"),
}

# ---------------------------------------------------------------------------
# Color name table (CSS3 subset)
# ---------------------------------------------------------------------------

_COLOR_NAMES = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "lime": (0, 255, 0),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
    "silver": (192, 192, 192),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "aqua": (0, 255, 255),
    "fuchsia": (255, 0, 255),
}


def _resolve_color(color, mode):
    """Resolve a color value to a list of ints suitable for _pil_native."""
    if color is None:
        color = 0
    if isinstance(color, str):
        c = color.strip().lower()
        if c.startswith("#"):
            hex_str = c[1:]
            if len(hex_str) == 3:
                hex_str = "".join(ch * 2 for ch in hex_str)
            if len(hex_str) == 6:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                color = (r, g, b)
            elif len(hex_str) == 8:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                a = int(hex_str[6:8], 16)
                color = (r, g, b, a)
            else:
                raise ValueError(f"bad color specifier: {c}")
        elif c in _COLOR_NAMES:
            color = _COLOR_NAMES[c]
        else:
            raise ValueError(f"unknown color specifier: {c}")
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
    return color


# ---------------------------------------------------------------------------
# Image class
# ---------------------------------------------------------------------------

class Image:
    """Wraps a native image handle returned by _pil_native."""

    def __init__(self, _handle):
        self._handle = _handle
        self.info = {}
        self.format = None

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
        """Return the pixel value at (x, y). Negative coordinates wrap around."""
        x, y = xy[0], xy[1]
        w, h = self.size
        if x < 0:
            x = x + w
        if y < 0:
            y = y + h
        if x < 0 or x >= w or y < 0 or y >= h:
            raise IndexError(f"pixel coordinate ({xy[0]}, {xy[1]}) out of range")
        return _pil_native.image_getpixel(self._handle, x, y)

    def putpixel(self, xy, color):
        """Set the pixel at (x, y) to *color*. Negative coordinates wrap around."""
        x, y = xy[0], xy[1]
        w, h = self.size
        if x < 0:
            x = x + w
        if y < 0:
            y = y + h
        if x < 0 or x >= w or y < 0 or y >= h:
            raise IndexError(f"pixel coordinate ({xy[0]}, {xy[1]}) out of range")
        if isinstance(color, int):
            color = (color,)
        _pil_native.image_putpixel(self._handle, x, y, list(color))

    # -- transforms ---------------------------------------------------------

    def resize(self, size, resample=None, **_kw):
        """Return a resized copy."""
        if isinstance(size, list):
            size = tuple(size)
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError(f"invalid size: {size}")
        if resample is not None:
            return Image(_pil_native.image_resize(self._handle, size[0], size[1], resample))
        return Image(_pil_native.image_resize(self._handle, size[0], size[1]))

    def thumbnail(self, size, resample=None, **_kw):
        """Modify the image in-place to fit within *size*, preserving aspect ratio.

        Only shrinks — never enlarges.
        """
        w, h = self.size
        max_w, max_h = size
        if w <= max_w and h <= max_h:
            return
        # Scale by the larger ratio to fit within bounds
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        new_im = self.resize((new_w, new_h), resample=resample)
        # Replace handle in-place
        _pil_native.image_close(self._handle)
        self._handle = new_im._handle
        new_im._handle = None  # prevent double-close

    def crop(self, box=None):
        """Return a cropped copy. *box* is (left, upper, right, lower).

        Float coordinates are rounded to the nearest integer.
        Raises ValueError if right < left or bottom < top.
        Crop regions outside the image boundaries are filled with zero.
        """
        if box is None:
            return self.copy()
        left, upper, right, lower = (int(round(v)) for v in box)
        if right < left:
            raise ValueError(
                f"Coordinate 'right' is less than 'left': {right} < {left}"
            )
        if lower < upper:
            raise ValueError(
                f"Coordinate 'lower' is less than 'upper': {lower} < {upper}"
            )
        iw, ih = self.size
        # Intersection of crop box with image bounds
        src_left = max(left, 0)
        src_upper = max(upper, 0)
        src_right = min(right, iw)
        src_lower = min(lower, ih)
        # If fully within image, delegate to Rust directly
        if left >= 0 and upper >= 0 and right <= iw and lower <= ih:
            return Image(_pil_native.image_crop(self._handle, [left, upper, right, lower]))
        # Otherwise create a zero-filled output and paste the valid intersection
        out_w = right - left
        out_h = lower - upper
        out = new(self.mode, (out_w, out_h), 0)
        if src_left < src_right and src_upper < src_lower:
            inner = Image(_pil_native.image_crop(self._handle, [src_left, src_upper, src_right, src_lower]))
            dst_left = src_left - left
            dst_upper = src_upper - upper
            _pil_native.image_paste(out._handle, inner._handle, dst_left, dst_upper)
        return out

    def rotate(self, angle, resample=None, expand=False, fillcolor=None, **_kw):
        """Return a rotated copy (counter-clockwise, in degrees).

        If *fillcolor* is given, the areas outside the rotation are filled with
        that color instead of black/transparent.
        """
        if fillcolor is None:
            return Image(_pil_native.image_rotate(self._handle, float(angle), bool(expand)))

        orig_mode = self.mode
        # Rotate in RGBA so empty areas become transparent (0,0,0,0)
        if orig_mode == "RGBA":
            rotated = Image(_pil_native.image_rotate(self._handle, float(angle), bool(expand)))
        else:
            rgba_handle = _pil_native.image_convert(self._handle, "RGBA")
            try:
                rot_handle = _pil_native.image_rotate(rgba_handle, float(angle), bool(expand))
            finally:
                _pil_native.image_close(rgba_handle)
            rotated = Image(rot_handle)

        # Resolve fillcolor to a 4-element [R, G, B, A] list
        fc = _resolve_color(fillcolor, "RGBA")
        while len(fc) < 4:
            fc.append(255)

        # Composite: replace transparent pixels with fillcolor
        rot_bytes = list(rotated.tobytes())
        out_bytes = []
        for i in range(0, len(rot_bytes), 4):
            if rot_bytes[i + 3] == 0:
                out_bytes.extend(fc)
            else:
                out_bytes.extend(rot_bytes[i : i + 4])

        w, h = rotated.size
        result = new("RGBA", (w, h), 0)
        _pil_native.image_putdata(result._handle, out_bytes)

        if orig_mode != "RGBA":
            return result.convert(orig_mode)
        return result

    def transpose(self, method):
        """Return a transposed copy (flip / rotate by 90-degree multiples)."""
        return Image(_pil_native.image_transpose(self._handle, method))

    def convert(self, mode=None, **_kw):
        """Return a copy converted to the given mode ('RGB', 'L', etc.)."""
        if mode is None:
            mode = "RGB"
        return Image(_pil_native.image_convert(self._handle, mode))

    # -- serialisation ------------------------------------------------------

    def save(self, fp, format=None, **params):
        """Save the image to *fp* (filename or file-like object)."""
        if format is None and isinstance(fp, str):
            ext = fp.rsplit(".", 1)[-1] if "." in fp else ""
            format = ext.lower() or "png"
        fmt = format or "png"
        quality = params.get("quality")
        if quality is not None:
            data = _pil_native.image_save(self._handle, fmt, int(quality))
        else:
            data = _pil_native.image_save(self._handle, fmt)
        if isinstance(fp, str):
            with __builtins__["open"](fp, "wb") if isinstance(__builtins__, dict) else __builtins__.open(fp, "wb") as f:
                f.write(data)
        else:
            fp.write(data)

    def tobytes(self):
        """Return raw pixel bytes."""
        return bytes(_pil_native.image_tobytes(self._handle))

    def frombytes(self, data):
        """Load raw pixel data into this image (in-place)."""
        w, h = self.size
        m = self.mode
        new_handle = _pil_native.image_frombytes(m, w, h, data)
        # Close old handle and replace
        if self._handle is not None:
            _pil_native.image_close(self._handle)
        self._handle = new_handle

    def getdata(self):
        """Return a flat sequence of pixel values."""
        raw = self.tobytes()
        m = self.mode
        bands = {"L": 1, "LA": 2, "RGB": 3, "RGBA": 4}.get(m, 3)
        if bands == 1:
            return list(raw)
        return [tuple(raw[i:i + bands]) for i in range(0, len(raw), bands)]

    def putdata(self, data):
        """Set all pixels from a flat sequence of pixel values."""
        m = self.mode
        bands = {"L": 1, "LA": 2, "RGB": 3, "RGBA": 4}.get(m, 3)
        flat = []
        for px in data:
            if isinstance(px, (tuple, list)):
                flat.extend(px)
            else:
                if bands == 1:
                    flat.append(int(px) & 0xFF)
                else:
                    v = int(px) & 0xFF
                    for _ in range(bands):
                        flat.append(v)
        _pil_native.image_putdata(self._handle, flat)

    # -- channel operations -------------------------------------------------

    def getbands(self):
        """Return a tuple of band names (e.g. ('R','G','B'))."""
        return _MODE_BANDS.get(self.mode, ("R", "G", "B"))

    def split(self):
        """Split the image into individual bands."""
        ids = _pil_native.image_split(self._handle)
        return tuple(Image(h) for h in ids)

    def getchannel(self, channel):
        """Return a single band as an 'L' mode image."""
        bands = self.getbands()
        if isinstance(channel, int):
            if channel < 0 or channel >= len(bands):
                raise ValueError(f"bad channel index: {channel}")
            idx = channel
        elif isinstance(channel, str):
            if channel not in bands:
                raise ValueError(f"bad channel name: {channel}")
            idx = bands.index(channel)
        else:
            raise ValueError(f"bad channel: {channel}")
        parts = self.split()
        return parts[idx]

    def getbbox(self):
        """Return bounding box of non-zero region, or None."""
        return _pil_native.image_getbbox(self._handle)

    # -- paste --------------------------------------------------------------

    def paste(self, im_or_color, box=None, mask=None):
        """Paste another image or color onto this image."""
        if isinstance(im_or_color, Image):
            x, y = 0, 0
            if box is not None:
                if isinstance(box, (tuple, list)):
                    x = box[0]
                    y = box[1]
            if mask is not None:
                # Masked paste: blend src into dst using mask as alpha
                src = im_or_color
                dw, dh = self.size
                sw, sh = src.size
                # Determine the number of bytes per pixel in dst
                n_dst = len(self.getbands())
                n_src = len(src.getbands())
                # Get mask as L (if it's RGBA use the alpha channel)
                if mask.mode == "RGBA":
                    mask_l = mask.split()[3]
                elif mask.mode == "L":
                    mask_l = mask
                else:
                    mask_l = mask.convert("L")
                mask_data = list(mask_l.getdata())
                # We use tobytes/frombytes for fast per-pixel work
                dst_bytes = bytearray(self.tobytes())
                src_bytes = bytearray(src.tobytes())
                for py in range(sh):
                    dy = y + py
                    if dy < 0 or dy >= dh:
                        continue
                    for px in range(sw):
                        dx = x + px
                        if dx < 0 or dx >= dw:
                            continue
                        alpha = mask_data[py * sw + px]
                        if alpha == 0:
                            continue
                        d_off = (dy * dw + dx) * n_dst
                        s_off = (py * sw + px) * n_src
                        if alpha == 255:
                            for c in range(min(n_dst, n_src)):
                                dst_bytes[d_off + c] = src_bytes[s_off + c]
                        else:
                            inv = 255 - alpha
                            for c in range(min(n_dst, n_src)):
                                dst_bytes[d_off + c] = (
                                    src_bytes[s_off + c] * alpha + dst_bytes[d_off + c] * inv
                                ) // 255
                _pil_native.image_putdata(self._handle, list(dst_bytes))
                return
            _pil_native.image_paste(self._handle, im_or_color._handle, x, y)
        elif isinstance(im_or_color, (tuple, list)):
            # Fill box with color
            w, h = self.size
            if box is None:
                box = (0, 0, w, h)
            fill_im = new(self.mode, (box[2] - box[0], box[3] - box[1]), tuple(im_or_color))
            _pil_native.image_paste(self._handle, fill_im._handle, box[0], box[1])
        elif isinstance(im_or_color, int):
            w, h = self.size
            if box is None:
                box = (0, 0, w, h)
            fill_im = new(self.mode, (box[2] - box[0], box[3] - box[1]), im_or_color)
            _pil_native.image_paste(self._handle, fill_im._handle, box[0], box[1])

    def alpha_composite(self, src, dest=(0, 0), source=None):
        """Composite *src* over this image in-place.

        *dest* is the (x, y) offset into this image where compositing starts.
        *source* is the optional (x, y) or (x, y, w, h) crop of *src* to use.
        """
        if not isinstance(dest, (tuple, list)) or len(dest) < 2:
            raise ValueError("dest must be a sequence of 2 integers")
        if source is not None:
            if not isinstance(source, (tuple, list)):
                raise ValueError("source must be a sequence")
            if len(source) == 2:
                src = src.crop((source[0], source[1], src.width, src.height))
            elif len(source) == 4:
                if source[1] < 0 or source[3] < 0:
                    raise ValueError("source coordinates cannot be negative")
                src = src.crop(source)
            else:
                raise ValueError("source must be 2 or 4 values")
        dx, dy = int(dest[0]), int(dest[1])
        # Determine the overlapping region
        sw, sh = src.size
        dw, dh = self.size
        # Clip to destination bounds
        src_x0 = max(-dx, 0)
        src_y0 = max(-dy, 0)
        src_x1 = min(sw, dw - dx)
        src_y1 = min(sh, dh - dy)
        if src_x1 <= src_x0 or src_y1 <= src_y0:
            return
        # Crop the src and dst regions that overlap
        src_region = src.crop((src_x0, src_y0, src_x1, src_y1))
        dst_x = dx + src_x0
        dst_y = dy + src_y0
        region_w = src_x1 - src_x0
        region_h = src_y1 - src_y0
        dst_region = self.crop((dst_x, dst_y, dst_x + region_w, dst_y + region_h))
        # Ensure both are RGBA for compositing
        if dst_region.mode != "RGBA":
            dst_region = dst_region.convert("RGBA")
        if src_region.mode != "RGBA":
            src_region = src_region.convert("RGBA")
        composited = alpha_composite(dst_region, src_region)
        # Paste result back
        if self.mode != "RGBA":
            composited = composited.convert(self.mode)
        _pil_native.image_paste(self._handle, composited._handle, dst_x, dst_y)

    def putalpha(self, alpha):
        """Set the alpha channel from an 'L' image or int value."""
        if self.mode != "RGBA":
            # Convert to RGBA first
            new_handle = _pil_native.image_convert(self._handle, "RGBA")
            _pil_native.image_close(self._handle)
            self._handle = new_handle
        w, h = self.size
        if isinstance(alpha, int):
            for y in range(h):
                for x in range(w):
                    px = self.getpixel((x, y))
                    self.putpixel((x, y), (px[0], px[1], px[2], alpha))
        elif isinstance(alpha, Image):
            for y in range(h):
                for x in range(w):
                    px = self.getpixel((x, y))
                    a = alpha.getpixel((x, y))
                    if isinstance(a, tuple):
                        a = a[0]
                    self.putpixel((x, y), (px[0], px[1], px[2], a))

    # -- statistics ---------------------------------------------------------

    def histogram(self, mask=None):
        """Return a histogram of pixel values (list of 256 * bands ints).

        If *mask* is given (an ``"L"`` image), only pixels where mask > 0
        are counted.
        """
        data = self.getdata()
        m = self.mode
        bands = len(_MODE_BANDS.get(m, ("R", "G", "B")))
        hist = [0] * (256 * bands)
        mask_data = mask.getdata() if mask is not None else None
        for i, px in enumerate(data):
            if mask_data is not None and mask_data[i] == 0:
                continue
            if isinstance(px, (tuple, list)):
                for b in range(bands):
                    hist[b * 256 + (px[b] & 0xFF)] += 1
            else:
                hist[px & 0xFF] += 1
        return hist

    def getcolors(self, maxcolors=256):
        """Return a list of (count, color) tuples."""
        data = self.getdata()
        counts = {}
        for px in data:
            key = px
            counts[key] = counts.get(key, 0) + 1
        if len(counts) > maxcolors:
            return None
        return [(count, color) for color, count in counts.items()]

    def getextrema(self):
        """Return min/max pixel values."""
        data = self.getdata()
        if not data:
            return None
        m = self.mode
        bands = len(_MODE_BANDS.get(m, ("R", "G", "B")))
        if bands == 1:
            return (min(data), max(data))
        mins = list(data[0])
        maxs = list(data[0])
        for px in data:
            for b in range(bands):
                if px[b] < mins[b]:
                    mins[b] = px[b]
                if px[b] > maxs[b]:
                    maxs[b] = px[b]
        return tuple((mins[b], maxs[b]) for b in range(bands))

    # -- point (pixel transform) --------------------------------------------

    def point(self, lut):
        """Apply a lookup table or function to each pixel."""
        if callable(lut):
            m = self.mode
            bands = len(_MODE_BANDS.get(m, ("R", "G", "B")))
            table = []
            for b in range(bands):
                for i in range(256):
                    table.append(int(lut(i)) & 0xFF)
            lut = table
        return Image(_pil_native.image_point(self._handle, list(lut)))

    # -- copy / close -------------------------------------------------------

    def copy(self):
        """Return an independent copy."""
        im = Image(_pil_native.image_copy(self._handle))
        im.info = dict(self.info)
        im.format = self.format
        return im

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

    def __eq__(self, other):
        if not isinstance(other, Image):
            return NotImplemented
        if self._handle is None or other._handle is None:
            return self._handle is other._handle
        return (self.mode == other.mode and
                self.size == other.size and
                self.tobytes() == other.tobytes())

    def __ne__(self, other):
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return eq
        return not eq

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
    im = Image(_pil_native.image_open(data))
    return im


def new(mode, size, color=0):
    """Create a new image with the given *mode* and *size*."""
    if isinstance(size, list):
        size = tuple(size)
    color = _resolve_color(color, mode)
    return Image(_pil_native.image_new(mode, size[0], size[1], color))


def frombytes(mode, size, data):
    """Create a new image from raw bytes."""
    return Image(_pil_native.image_frombytes(mode, size[0], size[1], data))


def merge(mode, channels):
    """Merge a sequence of single-band images into a multi-band image."""
    channel_ids = [ch._handle for ch in channels]
    return Image(_pil_native.image_merge(mode, channel_ids))


def alpha_composite(dst, src):
    """Porter-Duff 'over' compositing.  Both *dst* and *src* must be RGBA.

    Returns a new RGBA image with *src* composited over *dst*.
    """
    if dst.mode != "RGBA" or src.mode != "RGBA":
        raise ValueError("alpha_composite requires RGBA images")
    if dst.size != src.size:
        raise ValueError("images do not match in size")
    dst_bytes = bytearray(dst.tobytes())
    src_bytes = bytearray(src.tobytes())
    n = len(dst_bytes) // 4
    for i in range(n):
        off = i * 4
        sr, sg, sb, sa = src_bytes[off], src_bytes[off + 1], src_bytes[off + 2], src_bytes[off + 3]
        dr, dg, db, da = dst_bytes[off], dst_bytes[off + 1], dst_bytes[off + 2], dst_bytes[off + 3]
        if sa == 255:
            dst_bytes[off:off + 4] = bytes([sr, sg, sb, 255])
        elif sa > 0:
            sa_f = sa / 255.0
            da_f = da / 255.0
            out_a = sa_f + da_f * (1.0 - sa_f)
            if out_a > 0.0:
                inv = (1.0 - sa_f) * da_f / out_a
                dst_bytes[off] = min(255, round(sr * (sa_f / out_a) + dr * inv))
                dst_bytes[off + 1] = min(255, round(sg * (sa_f / out_a) + dg * inv))
                dst_bytes[off + 2] = min(255, round(sb * (sa_f / out_a) + db * inv))
                dst_bytes[off + 3] = min(255, round(out_a * 255.0))
    out = new("RGBA", dst.size, 0)
    _pil_native.image_putdata(out._handle, list(dst_bytes))
    return out


def getmodebands(mode):
    """Return the number of bands for a given mode."""
    return len(_MODE_BANDS.get(mode, ("R", "G", "B")))
