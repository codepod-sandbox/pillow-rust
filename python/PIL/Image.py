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
        if isinstance(size, list):
            size = tuple(size)
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

    def convert(self, mode=None, **_kw):
        """Return a copy converted to the given mode ('RGB', 'L', etc.)."""
        if mode is None:
            mode = "RGB"
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

    def histogram(self):
        """Return a histogram of pixel values (list of 256 * bands ints)."""
        data = self.getdata()
        m = self.mode
        bands = len(_MODE_BANDS.get(m, ("R", "G", "B")))
        hist = [0] * (256 * bands)
        for px in data:
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


def getmodebands(mode):
    """Return the number of bands for a given mode."""
    return len(_MODE_BANDS.get(mode, ("R", "G", "B")))
