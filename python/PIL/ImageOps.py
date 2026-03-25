"""
PIL.ImageOps — ready-made image processing operations.
"""

from PIL import Image


def autocontrast(image, cutoff=0, ignore=None):
    """Maximize image contrast by remapping pixel values to span 0-255."""
    if image.mode not in ("L", "RGB"):
        raise OSError(f"not supported for {image.mode!r} images")
    bands = image.getbands()
    if len(bands) == 1:
        # Single channel
        extrema = image.getextrema()
        lo, hi = extrema
        if lo >= hi:
            return image.point(lambda x: 0)
        scale = 255.0 / (hi - lo)
        offset = lo
        lut = [max(0, min(255, int((i - offset) * scale))) for i in range(256)]
        return image.point(lut)
    else:
        # Multi-channel: split, autocontrast each, merge
        channels = image.split()
        result_channels = []
        for ch in channels:
            result_channels.append(autocontrast(ch))
        return Image.merge(image.mode, result_channels)


def contain(image, size, method=None):
    """Resize to fit within *size*, preserving aspect ratio. Returns new image."""
    w, h = image.size
    max_w, max_h = size
    if w <= max_w and h <= max_h:
        return image.copy()
    scale = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), resample=method)


def fit(image, size, method=None, centering=(0.5, 0.5)):
    """Resize and crop to fill *size* exactly, preserving aspect ratio."""
    target_w, target_h = size
    src_w, src_h = image.size
    # Scale so the smaller dimension matches the target
    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), resample=method)
    # Crop from center
    cx, cy = centering
    left = int((new_w - target_w) * cx)
    top = int((new_h - target_h) * cy)
    return resized.crop((left, top, left + target_w, top + target_h))


def pad(image, size, method=None, color=None, centering=(0.5, 0.5)):
    """Resize to fit within *size* and pad to fill exactly."""
    target_w, target_h = size
    # Contain first
    contained = contain(image, size, method=method)
    cw, ch = contained.size
    if cw == target_w and ch == target_h:
        return contained
    # Create canvas with fill color
    fill = color if color is not None else 0
    out = Image.new(image.mode, (target_w, target_h), fill)
    # Paste centered
    cx, cy = centering
    left = int((target_w - cw) * cx)
    top = int((target_h - ch) * cy)
    out.paste(contained, (left, top))
    return out


def expand(image, border=0, fill=0):
    """Add a border around the image.

    *border* can be an int, 2-tuple (left/right, top/bottom),
    or 4-tuple (left, top, right, bottom).
    """
    if isinstance(border, int):
        left = top = right = bottom = border
    elif len(border) == 2:
        left = right = border[0]
        top = bottom = border[1]
    elif len(border) == 4:
        left, top, right, bottom = border
    else:
        raise ValueError("border must be int, 2-tuple, or 4-tuple")
    w, h = image.size
    out = Image.new(image.mode, (w + left + right, h + top + bottom), fill)
    out.paste(image, (left, top))
    return out


def flip(image):
    """Flip the image vertically (top to bottom)."""
    return image.transpose(Image.FLIP_TOP_BOTTOM)


def mirror(image):
    """Flip the image horizontally (left to right)."""
    return image.transpose(Image.FLIP_LEFT_RIGHT)


def grayscale(image):
    """Convert the image to grayscale."""
    return image.convert("L")


def invert(image):
    """Invert all pixel values (255 - v for each channel).

    Supports L and RGB modes.
    """
    if image.mode not in ("L", "RGB"):
        raise OSError(f"not supported for {image.mode!r} images")
    return image.point(lambda v: 255 - v)


def scale(image, factor, resample=None):
    """Return a rescaled image by *factor*.

    A factor greater than 1 expands the image; less than 1 shrinks it.
    """
    if factor < 0:
        raise ValueError("the factor must be greater than 0")
    w, h = image.size
    new_w = max(1, round(w * factor))
    new_h = max(1, round(h * factor))
    return image.resize((new_w, new_h), resample=resample)
