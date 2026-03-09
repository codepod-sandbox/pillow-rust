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

# Transform methods
AFFINE = 0
PERSPECTIVE = 1

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

    # -- paste --------------------------------------------------------------

    def paste(self, im, box=None, mask=None):
        """Paste *im* onto this image. *box* is (x, y) or (x, y, x1, y1)."""
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

    def histogram(self):
        """Return histogram as list of ints (256 values per channel)."""
        return list(_pil_native.image_histogram(self._handle))

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
        """Return a copy converted to the given mode ('RGB', 'L', 'LA', 'RGBA', '1')."""
        if mode == "1":
            # Binary mode: threshold at 128
            gray = self if self.mode == "L" else Image(_pil_native.image_convert(self._handle, "L"))
            return gray.point(lambda x: 255 if x >= 128 else 0)
        return Image(_pil_native.image_convert(self._handle, mode))

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
        return Image(_pil_native.image_copy(self._handle))

    def close(self):
        """Release the underlying native handle."""
        if self._handle is not None:
            _pil_native.image_close(self._handle)
            self._handle = None

    # -- bulk pixel access --------------------------------------------------

    def getdata(self):
        """Return contents as a flat list of pixel values."""
        return _pil_native.image_getdata(self._handle)

    def putdata(self, data):
        """Replace image data from a flat sequence of pixel values."""
        w, h = self.size
        m = self.mode
        if m == "L":
            for i, v in enumerate(data):
                x, y = i % w, i // w
                if y < h:
                    val = v if isinstance(v, int) else v[0]
                    _pil_native.image_putpixel(self._handle, x, y, [val])
        else:
            for i, v in enumerate(data):
                x, y = i % w, i // w
                if y < h:
                    _pil_native.image_putpixel(self._handle, x, y, list(v))

    def point(self, lut, mode=None):
        """Apply a lookup table to each pixel. *lut* is a list of 256 values."""
        if callable(lut):
            lut = [lut(i) for i in range(256)]
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

    def alpha_composite(self, im, dest=(0, 0), source=(0, 0)):
        """Alpha composite *im* over this image."""
        return Image(_pil_native.image_alpha_composite(self._handle, im._handle))

    # -- channel access -----------------------------------------------------

    def getchannel(self, channel):
        """Return a single channel as an L-mode image.
        *channel* can be an index (0, 1, 2, ...) or a name ('R', 'G', 'B', 'A').
        """
        if isinstance(channel, str):
            channel_map = {
                "R": 0, "G": 1, "B": 2, "A": 3,
                "L": 0,
            }
            idx = channel_map.get(channel.upper())
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
        """No-op — pixels are always loaded in our implementation."""
        pass

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
    img = Image(_pil_native.image_open(data))
    if isinstance(fp, str) and "." in fp:
        ext = fp.rsplit(".", 1)[-1].upper()
        fmt_map = {"JPG": "JPEG", "PNG": "PNG", "GIF": "GIF", "BMP": "BMP",
                   "TIFF": "TIFF", "TIF": "TIFF", "WEBP": "WEBP", "JPEG": "JPEG"}
        img.format = fmt_map.get(ext, ext)
    return img


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
