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

# Transform methods
AFFINE = 0
PERSPECTIVE = 1

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
# PixelAccess — returned by Image.load()
# ---------------------------------------------------------------------------

class PixelAccess:
    """Pixel access object supporting px[x, y] read/write."""

    def __init__(self, image):
        self._image = image

    def __getitem__(self, xy):
        return self._image.getpixel(xy)

    def __setitem__(self, xy, value):
        self._image.putpixel(xy, value)


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
        if hasattr(self, '_mode_override') and self._mode_override is not None:
            return self._mode_override
        return _pil_native.image_mode(self._handle)

    # -- pixel access -------------------------------------------------------

    def _resolve_xy(self, xy):
        """Resolve (x, y) supporting negative indices; raise IndexError if out of bounds."""
        x, y = int(xy[0]), int(xy[1])
        w, h = self.size
        if x < 0:
            x += w
        if y < 0:
            y += h
        if x < 0 or x >= w or y < 0 or y >= h:
            raise IndexError(f"pixel coordinate ({xy[0]}, {xy[1]}) out of range for {w}x{h} image")
        return x, y

    def getpixel(self, xy):
        """Return the pixel value at (x, y)."""
        x, y = self._resolve_xy(xy)
        return _pil_native.image_getpixel(self._handle, x, y)

    def putpixel(self, xy, color):
        """Set the pixel at (x, y) to *color*."""
        x, y = self._resolve_xy(xy)
        if isinstance(color, int):
            color = (color,)
        _pil_native.image_putpixel(self._handle, x, y, list(color))

    # -- paste --------------------------------------------------------------

    def paste(self, im, box=None, mask=None):
        """Paste *im* onto this image.

        *im* can be an Image, a color integer, or a color tuple.
        *box* is (x, y) or (x, y, x1, y1).
        """
        # Handle color fill: paste(color, box) fills the region
        if isinstance(im, (int, tuple)):
            color = im
            if isinstance(color, int):
                if self.mode in ("RGB", "RGBA"):
                    color = (color, color, color) + ((255,) if self.mode == "RGBA" else ())
                elif self.mode == "L":
                    color = (color,)
                elif self.mode == "LA":
                    color = (color, 255)
                else:
                    color = (color,)
            if box is None:
                w, h = self.size
                fill_box = (0, 0, w, h)
            elif len(box) == 2:
                fill_box = (box[0], box[1], self.size[0], self.size[1])
            else:
                fill_box = box
            # Create a solid-color image to paste
            bw = fill_box[2] - fill_box[0]
            bh = fill_box[3] - fill_box[1]
            if bw <= 0 or bh <= 0:
                return
            fill_im = new(self.mode, (bw, bh), color)
            x, y = fill_box[0], fill_box[1]
            if mask is not None:
                mask_handle = mask._handle if hasattr(mask, '_handle') else None
                if mask_handle is not None:
                    _pil_native.image_paste(self._handle, fill_im._handle, x, y, mask_handle)
                    return
            _pil_native.image_paste(self._handle, fill_im._handle, x, y)
            return

        if box is None:
            x, y = 0, 0
        elif len(box) == 2:
            x, y = box
        else:
            x, y = box[0], box[1]
        src_handle = im._handle if hasattr(im, '_handle') else im
        mask_handle = mask._handle if mask is not None and hasattr(mask, '_handle') else None
        if mask_handle is not None:
            _pil_native.image_paste(self._handle, src_handle, x, y, mask_handle)
        else:
            _pil_native.image_paste(self._handle, src_handle, x, y)

    # -- channel ops --------------------------------------------------------

    def split(self):
        """Split into individual channels as L-mode images."""
        ids = _pil_native.image_split(self._handle)
        return tuple(Image(h) for h in ids)

    # -- statistics ---------------------------------------------------------

    def histogram(self, mask=None):
        """Return a histogram of pixel values (list of 256 * bands ints).

        If *mask* is given (an ``"L"`` image), only pixels where mask > 0
        are counted.
        """
        if mask is None:
            h = list(_pil_native.image_histogram(self._handle))
            # Mode "1" returns a 2-entry histogram [count_black, count_white]
            if self.mode == "1":
                black = h[0]
                white = h[255]
                return [black, white]
            return h
        # Masked histogram: compute in Python
        data = self.getdata()
        m = self.mode
        bands = len(_MODE_BANDS.get(m, ("R", "G", "B")))
        hist = [0] * (256 * bands)
        mask_data = mask.getdata()
        for i, px in enumerate(data):
            mv = mask_data[i] if i < len(mask_data) else 0
            mv_val = mv if isinstance(mv, int) else mv[0]
            if mv_val == 0:
                continue
            if isinstance(px, (tuple, list)):
                for b in range(bands):
                    hist[b * 256 + (px[b] & 0xFF)] += 1
            else:
                hist[px & 0xFF] += 1
        return hist

    def getbbox(self):
        """Return bounding box of non-zero pixels, or None."""
        return _pil_native.image_getbbox(self._handle)

    def getextrema(self):
        """Return min/max pixel value(s)."""
        return _pil_native.image_getextrema(self._handle)

    # -- thumbnail ----------------------------------------------------------

    def thumbnail(self, size, resample=None, **_kw):
        """Modify in place to fit within *size*, preserving aspect ratio."""
        w, h = self.size
        tw, th = size
        if w <= tw and h <= th:
            return  # already fits, PIL never upsizes
        ratio = min(tw / w, th / h)
        new_w = max(1, int(w * ratio))
        new_h = max(1, int(h * ratio))
        if resample is not None:
            resized = Image(_pil_native.image_resize(self._handle, new_w, new_h, resample))
        else:
            resized = Image(_pil_native.image_resize(self._handle, new_w, new_h))
        # Replace our handle
        old = self._handle
        self._handle = resized._handle
        resized._handle = None  # prevent resized.__del__ from closing it
        _pil_native.image_close(old)

    # -- transforms ---------------------------------------------------------

    def resize(self, size, resample=None, **_kw):
        """Return a resized copy."""
        w, h = int(size[0]), int(size[1])
        if w <= 0 or h <= 0:
            raise ValueError(f"invalid size: {size}")
        if resample is not None:
            return Image(_pil_native.image_resize(self._handle, w, h, resample))
        return Image(_pil_native.image_resize(self._handle, w, h))

    def crop(self, box=None):
        """Return a cropped copy. *box* is (left, upper, right, lower)."""
        if box is None:
            return self.copy()
        x0, y0, x1, y1 = round(box[0]), round(box[1]), round(box[2]), round(box[3])
        if x1 < x0:
            raise ValueError(f"crop right ({x1}) must be >= left ({x0})")
        if y1 < y0:
            raise ValueError(f"crop lower ({y1}) must be >= upper ({y0})")
        w, h = self.size
        # If box is fully within bounds, fast path
        if x0 >= 0 and y0 >= 0 and x1 <= w and y1 <= h and x1 >= x0 and y1 >= y0:
            return Image(_pil_native.image_crop(self._handle, [x0, y0, x1, y1]))
        # Wide crop: create output filled with black, paste valid region
        out_w = max(0, x1 - x0)
        out_h = max(0, y1 - y0)
        out = new(self.mode, (out_w, out_h), 0)
        if out_w == 0 or out_h == 0:
            return out
        src_x0 = max(0, x0)
        src_y0 = max(0, y0)
        src_x1 = min(w, x1)
        src_y1 = min(h, y1)
        if src_x0 >= src_x1 or src_y0 >= src_y1:
            return out
        piece = Image(_pil_native.image_crop(self._handle, [src_x0, src_y0, src_x1, src_y1]))
        _pil_native.image_paste(out._handle, piece._handle, src_x0 - x0, src_y0 - y0)
        return out

    def rotate(self, angle, resample=None, expand=False, fillcolor=None, **_kw):
        """Return a rotated copy (counter-clockwise, in degrees).

        If *fillcolor* is given, areas outside the rotation are filled with
        that color instead of black/transparent.
        """
        if fillcolor is None:
            return Image(_pil_native.image_rotate(self._handle, float(angle), expand))

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

        # Resolve fillcolor to a 4-element list [R, G, B, A]
        fc = _resolve_color(fillcolor, "RGBA")
        while len(fc) < 4:
            fc.append(255)

        # Replace transparent pixels with fillcolor
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

    def convert(self, mode=None, matrix=None, **_kw):
        """Return a copy converted to the given mode ('RGB', 'L', 'LA', 'RGBA', '1')."""
        if mode is None:
            mode = "RGB"
        if matrix is not None:
            return self._convert_with_matrix(mode, matrix)
        if mode == "1":
            # Binary mode: threshold at 128
            gray = self if self.mode in ("L", "1") else Image(_pil_native.image_convert(self._handle, "L"))
            out = gray.point(lambda x: 255 if x >= 128 else 0)
            out._mode_override = "1"
            return out
        return Image(_pil_native.image_convert(self._handle, mode))

    def _convert_with_matrix(self, mode, matrix):
        """Apply a color matrix transformation."""
        src_mode = self.mode
        w, h = self.size
        matrix = list(matrix)

        if mode == "L" and len(matrix) == 4:
            # Single channel output: dot product of RGB with [r, g, b, offset]
            rc, gc, bc, off = matrix
            out = new("L", (w, h), 0)
            for y in range(h):
                for x in range(w):
                    px = self.getpixel((x, y))
                    if isinstance(px, (tuple, list)):
                        r, g, b = px[0], px[1], px[2]
                    else:
                        r = g = b = int(px)
                    v = int(rc * r + gc * g + bc * b + off)
                    out.putpixel((x, y), max(0, min(255, v)))
            return out
        elif mode == "RGB" and len(matrix) == 12:
            # 3x4 matrix: 3 channels, each with [r_coeff, g_coeff, b_coeff, offset]
            out = new("RGB", (w, h), 0)
            for y in range(h):
                for x in range(w):
                    px = self.getpixel((x, y))
                    if isinstance(px, (tuple, list)):
                        r, g, b = px[0], px[1], px[2]
                    else:
                        r = g = b = int(px)
                    nr = int(matrix[0]*r + matrix[1]*g + matrix[2]*b + matrix[3])
                    ng = int(matrix[4]*r + matrix[5]*g + matrix[6]*b + matrix[7])
                    nb = int(matrix[8]*r + matrix[9]*g + matrix[10]*b + matrix[11])
                    out.putpixel((x, y), (max(0, min(255, nr)), max(0, min(255, ng)), max(0, min(255, nb))))
            return out
        else:
            raise ValueError(f"unsupported matrix conversion: {src_mode} -> {mode} with {len(matrix)} matrix values")

    def transform(self, size, method, data=None, resample=0, fill=1, fillcolor=None):
        """Apply a geometric transform and return a new image."""
        coeffs = [float(v) for v in data]
        if method == AFFINE:
            return Image(_pil_native.image_transform_affine(
                self._handle, size[0], size[1], coeffs))
        elif method == PERSPECTIVE:
            return Image(_pil_native.image_transform_perspective(
                self._handle, size[0], size[1], coeffs))
        else:
            raise ValueError(f"unsupported transform method: {method}")

    # -- serialisation ------------------------------------------------------

    def save(self, fp, format=None, **params):
        """Save the image to *fp* (filename or file-like object).

        Keyword arguments are format-specific. JPEG supports ``quality=``
        (1-95, default 75).
        """
        if format is None and isinstance(fp, str):
            ext = fp.rsplit(".", 1)[-1] if "." in fp else ""
            format = ext.lower() or "png"
        fmt = format or "png"
        quality = params.get("quality")
        if quality is not None:
            data = _pil_native.image_save_with_quality(self._handle, fmt, int(quality))
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

    # -- copy / close -------------------------------------------------------

    def copy(self):
        """Return an independent copy."""
        out = Image(_pil_native.image_copy(self._handle))
        out.info = self.info.copy()
        return out

    def close(self):
        """Release the underlying native handle."""
        if self._handle is not None:
            _pil_native.image_close(self._handle)
            self._handle = None

    def frombytes(self, data):
        """Load image data from raw bytes (in-place, same mode and size)."""
        _pil_native.image_putdata(self._handle, list(data))

    # -- bulk pixel access --------------------------------------------------

    def getdata(self):
        """Return contents as a flat list of pixel values."""
        return _pil_native.image_getdata(self._handle)

    def putdata(self, data, scale=1.0, offset=0.0):
        """Replace image data from a flat sequence of pixel values."""
        m = self.mode
        bands = {"L": 1, "LA": 2, "RGB": 3, "RGBA": 4}.get(m, 3)
        flat = []
        for px in data:
            if isinstance(px, (tuple, list)):
                if scale != 1.0 or offset != 0.0:
                    flat.extend(max(0, min(255, int(v * scale + offset))) for v in px)
                else:
                    flat.extend(px)
            else:
                if scale != 1.0 or offset != 0.0:
                    v = max(0, min(255, int(px * scale + offset)))
                else:
                    v = int(px) & 0xFF
                if bands == 1:
                    flat.append(v)
                else:
                    for _ in range(bands):
                        flat.append(v)
        _pil_native.image_putdata(self._handle, flat)

    def point(self, lut, mode=None):
        """Apply a lookup table to each pixel. *lut* is a list of 256 values."""
        bands = len(self.getbands())
        if callable(lut):
            lut = [lut(i) for i in range(256)] * bands
        elif len(lut) == 256 and bands > 1:
            lut = list(lut) * bands
        out = Image(_pil_native.image_point(self._handle, [int(v) & 0xFF for v in lut]))
        target_mode = mode or self.mode
        if out.mode != target_mode:
            out = out.convert(target_mode)
        return out

    # -- compositing -------------------------------------------------------

    def quantize(self, colors=256, method=None, kmeans=0, palette=None, dither=1):
        """Return a quantized copy with at most *colors* distinct colors."""
        return Image(_pil_native.image_quantize(self._handle, int(colors)))

    def getcolors(self, maxcolors=256):
        """Return a list of (count, color) tuples, or None if too many colors."""
        return _pil_native.image_getcolors(self._handle, int(maxcolors))

    def alpha_composite(self, im, dest=(0, 0), source=None):
        """Alpha composite *im* over this image in-place.

        *dest* is the (x, y) offset into this image where compositing starts.
        *source* is the optional (x, y) or (x, y, w, h) crop of *im* to use.
        """
        src = im
        if source is not None:
            if not isinstance(source, (tuple, list)):
                raise ValueError("source must be a sequence")
            if len(source) == 2:
                src = im.crop((source[0], source[1], im.width, im.height))
            elif len(source) == 4:
                src = im.crop(source)
            else:
                raise ValueError("source must be 2 or 4 values")
        dx, dy = int(dest[0]), int(dest[1])
        sw, sh = src.size
        dw, dh = self.size
        src_x0 = max(-dx, 0)
        src_y0 = max(-dy, 0)
        src_x1 = min(sw, dw - dx)
        src_y1 = min(sh, dh - dy)
        if src_x1 <= src_x0 or src_y1 <= src_y0:
            return
        src_region = src.crop((src_x0, src_y0, src_x1, src_y1))
        dst_x = dx + src_x0
        dst_y = dy + src_y0
        region_w = src_x1 - src_x0
        region_h = src_y1 - src_y0
        dst_region = self.crop((dst_x, dst_y, dst_x + region_w, dst_y + region_h))
        if dst_region.mode != "RGBA":
            dst_region = dst_region.convert("RGBA")
        if src_region.mode != "RGBA":
            src_region = src_region.convert("RGBA")
        composited = alpha_composite(dst_region, src_region)
        if self.mode != "RGBA":
            composited = composited.convert(self.mode)
        _pil_native.image_paste(self._handle, composited._handle, dst_x, dst_y)

    # -- channel access -----------------------------------------------------

    def getchannel(self, channel):
        """Return a single channel as an L-mode image.
        *channel* can be an index (0, 1, 2, ...) or a name ('R', 'G', 'B', 'A').
        """
        if isinstance(channel, str):
            ch = channel.upper()
            # LA mode: L=0, A=1
            if self.mode == "LA" and ch == "A":
                idx = 1
            else:
                channel_map = {
                    "R": 0, "G": 1, "B": 2, "A": 3,
                    "L": 0,
                }
                idx = channel_map.get(ch)
            if idx is None:
                raise ValueError(f"unknown channel name: {channel}")
        else:
            idx = int(channel)
        bands = self.split()
        if idx < 0 or idx >= len(bands):
            raise ValueError(f"channel index {idx} out of range for mode {self.mode}")
        return bands[idx]

    # -- reduce / downsample ------------------------------------------------

    def reduce(self, factor, box=None):
        """Return a copy reduced by integer *factor*."""
        if isinstance(factor, int):
            fx, fy = factor, factor
        else:
            fx, fy = factor
        if box is not None:
            src = self.crop(box)
        else:
            src = self
        w, h = src.size
        new_w = max(1, w // fx)
        new_h = max(1, h // fy)
        return src.resize((new_w, new_h))

    # -- stubs for compatibility -------------------------------------------

    def load(self):
        """Return a pixel access object supporting px[x, y] and px[x, y] = v."""
        return PixelAccess(self)

    def show(self, title=None):
        """No-op — display is not available in sandbox."""
        pass

    def tell(self):
        """Return current frame number (always 0 for single-frame images)."""
        return 0

    def seek(self, frame):
        """Seek to frame number. Only frame 0 is supported."""
        if frame != 0:
            raise EOFError("no more frames")

    @property
    def n_frames(self):
        """Number of frames (always 1 for non-animated images)."""
        return 1

    @property
    def is_animated(self):
        """Whether the image has multiple frames."""
        return False

    # -- filter -------------------------------------------------------------

    def filter(self, f):
        """Apply *f* (an ImageFilter object) and return a new Image."""
        args = getattr(f, "args", None) or []
        return Image(_pil_native.image_filter(self._handle, f.name, args))

    # -- channel utilities --------------------------------------------------

    def getbands(self):
        """Return a tuple of band names (e.g. ('R','G','B'))."""
        return _MODE_BANDS.get(self.mode, ("R", "G", "B"))

    def putalpha(self, alpha):
        """Set the alpha channel from an 'L' image or int value."""
        if self.mode != "RGBA":
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

    # -- dunder helpers -----------------------------------------------------

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
    img = Image(_pil_native.image_open(data))
    if isinstance(fp, str) and "." in fp:
        ext = fp.rsplit(".", 1)[-1].upper()
        fmt_map = {"JPG": "JPEG", "PNG": "PNG", "GIF": "GIF", "BMP": "BMP",
                   "TIFF": "TIFF", "TIF": "TIFF", "WEBP": "WEBP", "JPEG": "JPEG"}
        img.format = fmt_map.get(ext, ext)
    return img


def new(mode, size, color=0):
    """Create a new image with the given *mode* and *size*."""
    # Mode "1" (binary) is stored as L with values 0 or 255
    if mode == "1":
        if isinstance(color, str):
            from PIL import ImageColor
            color = ImageColor.getcolor(color, "1")
        fill = 255 if color else 0
        im = Image(_pil_native.image_new("L", size[0], size[1], [fill]))
        im._mode_override = "1"
        return im
    if isinstance(color, str):
        # Named color support: "red", "#ff0000", "rgb(255,0,0)", etc.
        from PIL import ImageColor
        color = ImageColor.getcolor(color, mode)
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


def frombytes(mode, size, data):
    """Create an image from raw pixel *data*."""
    return Image(_pil_native.image_frombytes(mode, size[0], size[1], data))


def fromarray(obj, mode=None):
    """Create an image from a numpy-like array.

    The array must expose ``.shape``, ``.dtype``, and ``.tobytes()``
    (or be convertible via ``bytes(obj)``).
    """
    shape = obj.shape
    if len(shape) == 2:
        h, w = shape
        if mode is None:
            mode = "L"
    elif len(shape) == 3:
        h, w, c = shape
        if mode is None:
            mode = {1: "L", 2: "LA", 3: "RGB", 4: "RGBA"}.get(c, "RGBA")
    else:
        raise ValueError("unsupported array shape: " + str(shape))
    raw = obj.tobytes() if hasattr(obj, 'tobytes') else bytes(obj)
    return frombytes(mode, (w, h), raw)


def merge(mode, bands):
    """Merge individual L-mode band images into a multi-channel image."""
    ids = [b._handle for b in bands]
    return Image(_pil_native.image_merge(mode, ids))


def blend(im1, im2, alpha):
    """Linear interpolation: out = im1 * (1 - alpha) + im2 * alpha."""
    out = Image(_pil_native.image_blend(im1._handle, im2._handle, float(alpha)))
    if im1.mode != "RGBA":
        out = out.convert(im1.mode)
    return out


def eval(image, func):
    """Apply *func* to each pixel value and return a new image."""
    return image.point(func)


def linear_gradient(mode):
    """Create a 256x256 linear gradient image."""
    im = new("L", (256, 256), 0)
    for y in range(256):
        for x in range(256):
            im.putpixel((x, y), y)
    if mode != "L":
        im = im.convert(mode)
    return im


def radial_gradient(mode):
    """Create a 256x256 radial gradient image."""
    im = new("L", (256, 256), 0)
    cx, cy = 127.5, 127.5
    for y in range(256):
        for x in range(256):
            dx = x - cx
            dy = y - cy
            d = int(min(255, (dx * dx + dy * dy) ** 0.5 * 255 / 180.3))
            im.putpixel((x, y), d)
    if mode != "L":
        im = im.convert(mode)
    return im


def composite(im1, im2, mask):
    """Composite two images using a mask."""
    out = Image(_pil_native.image_composite(im1._handle, im2._handle, mask._handle))
    if im1.mode != "RGBA":
        out = out.convert(im1.mode)
    return out


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
