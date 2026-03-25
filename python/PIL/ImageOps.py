"""
PIL.ImageOps — ready-made image processing operations.
"""

from PIL import Image


def autocontrast(image, cutoff=0, ignore=None, mask=None, preserve_tone=False):
    """Maximize image contrast by remapping pixel values to span 0-255.

    *cutoff* percent of lightest/darkest pixels are removed from the
    histogram before computing the remap.  Can be a single value or a
    ``(low, high)`` tuple.

    If *preserve_tone* is ``True``, a single LUT (derived from the first
    channel) is applied identically to every channel so relative tones
    are preserved.

    *mask* is an optional ``"L"`` image; only pixels where the mask is
    non-zero are used to compute the histogram.
    """
    if image.mode not in ("L", "RGB"):
        raise OSError(f"not supported for {image.mode!r} images")

    histogram = image.histogram(mask)
    num_channels = len(histogram) // 256

    lut = []
    for layer in range(num_channels):
        h = histogram[layer * 256 : (layer + 1) * 256]
        if cutoff:
            if isinstance(cutoff, (list, tuple)):
                cut_lo_pct, cut_hi_pct = cutoff[0], cutoff[1]
            else:
                cut_lo_pct = cut_hi_pct = cutoff
            n = sum(h)
            cut_lo = n * cut_lo_pct // 100
            cut_hi = n * cut_hi_pct // 100
            lo = 0
            for lo in range(256):
                cut_lo -= h[lo]
                if cut_lo < 0:
                    break
            hi = 255
            for hi in range(255, -1, -1):
                cut_hi -= h[hi]
                if cut_hi < 0:
                    break
        else:
            lo = 0
            hi = 255
            while lo < 256 and not h[lo]:
                lo += 1
            while hi >= 0 and not h[hi]:
                hi -= 1
        if hi <= lo:
            lut.extend(range(256))
            continue
        scale = 255.0 / (hi - lo)
        offset = -lo * scale
        for ix in range(256):
            v = int(ix * scale + offset)
            lut.append(max(0, min(255, v)))

    if preserve_tone:
        lut = lut[:256] * num_channels

    return image.point(lut)


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
