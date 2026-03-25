"""
PIL.ImageOps — standard image operations.
"""

import _pil_native
from PIL import Image as ImageModule
from PIL.Image import Image


def grayscale(image):
    """Convert to greyscale."""
    return image.convert("L")


def flip(image):
    """Flip top to bottom."""
    return image.transpose(ImageModule.FLIP_TOP_BOTTOM)


def mirror(image):
    """Flip left to right."""
    return image.transpose(ImageModule.FLIP_LEFT_RIGHT)


def invert(image):
    """Invert (negate) the image."""
    if image.mode not in ("L", "RGB"):
        raise OSError(f"not supported for {image.mode!r} images")
    return Image(_pil_native.image_invert(image._handle))


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


def pad(image, size, color=0, centering=(0.5, 0.5)):
    """Resize and pad to fit *size* exactly, preserving aspect ratio."""
    w, h = image.size
    tw, th = size
    ratio = min(tw / w, th / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    resized = image.resize((new_w, new_h))
    if isinstance(color, int):
        if image.mode in ("RGB", "RGBA"):
            c = [color, color, color] + ([255] if image.mode == "RGBA" else [])
        else:
            c = [color]
    elif isinstance(color, tuple):
        c = list(color)
    else:
        c = [color]
    out = ImageModule.new(image.mode, size, c)
    x = int((tw - new_w) * centering[0])
    y = int((th - new_h) * centering[1])
    out.paste(resized, (x, y))
    return out


def contain(image, size, method=None):
    """Resize to fit within *size*, preserving aspect ratio (no padding)."""
    w, h = image.size
    tw, th = size
    ratio = min(tw / w, th / h)
    if ratio >= 1:
        return image.copy()
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    if method is not None:
        return image.resize((new_w, new_h), resample=method)
    return image.resize((new_w, new_h))


def cover(image, size, method=None):
    """Resize to cover *size* (crop to fill), preserving aspect ratio."""
    w, h = image.size
    tw, th = size
    ratio = max(tw / w, th / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    if method is not None:
        resized = image.resize((new_w, new_h), resample=method)
    else:
        resized = image.resize((new_w, new_h))
    # Center crop
    x = (new_w - tw) // 2
    y = (new_h - th) // 2
    return resized.crop((x, y, x + tw, y + th))


def fit(image, size, method=None, bleed=0.0, centering=(0.5, 0.5)):
    """Resize and crop to fill *size* exactly (alias for cover + crop)."""
    return cover(image, size, method=method)


def scale(image, factor, resample=None):
    """Scale by a given *factor*."""
    if factor < 0:
        raise ValueError(f"scale factor must be non-negative, got {factor}")
    w, h = image.size
    new_w = max(1, int(w * factor))
    new_h = max(1, int(h * factor))
    if resample is not None:
        return image.resize((new_w, new_h), resample=resample)
    return image.resize((new_w, new_h))


def equalize(image, mask=None):
    """Equalize the image histogram."""
    h = image.histogram()
    mode = image.mode
    if mode == "L":
        bands = 1
    elif mode in ("RGB", "RGBA"):
        bands = 3
    else:
        bands = 1

    w, ht = image.size
    n = w * ht
    lut = []
    for b in range(bands):
        histo = h[b * 256 : (b + 1) * 256]
        # Build cumulative distribution
        step = (n - histo[0]) / 255.0 if n > histo[0] else 0
        if step == 0:
            lut.extend(list(range(256)))
        else:
            cumulative = 0
            for i in range(256):
                cumulative += histo[i]
                lut.append(max(0, min(255, int((cumulative - histo[0]) / step + 0.5))))

    if bands == 1:
        return image.point(lut)
    else:
        # For RGB/RGBA, apply per-channel LUT
        channels = image.split()
        out_channels = []
        for i in range(bands):
            band_lut = lut[i * 256 : (i + 1) * 256]
            out_channels.append(channels[i].point(band_lut))
        if mode == "RGBA":
            out_channels.append(channels[3])  # preserve alpha
        return ImageModule.merge(mode, out_channels)


def solarize(image, threshold=128):
    """Invert all pixel values above *threshold*."""
    lut = []
    for i in range(256):
        if i < threshold:
            lut.append(i)
        else:
            lut.append(255 - i)

    mode = image.mode
    if mode == "L":
        return image.point(lut)
    elif mode in ("RGB", "RGBA"):
        channels = image.split()
        bands = 3
        out_channels = [channels[i].point(lut) for i in range(bands)]
        if mode == "RGBA":
            out_channels.append(channels[3])
        return ImageModule.merge(mode, out_channels)
    return image.point(lut)


def posterize(image, bits):
    """Reduce the number of bits for each colour channel to *bits*."""
    if bits < 1 or bits > 8:
        raise ValueError("bits must be between 1 and 8")
    mask = ~(0xFF >> bits) & 0xFF
    lut = [i & mask for i in range(256)]

    mode = image.mode
    if mode == "L":
        return image.point(lut)
    elif mode in ("RGB", "RGBA"):
        channels = image.split()
        bands = 3
        out_channels = [channels[i].point(lut) for i in range(bands)]
        if mode == "RGBA":
            out_channels.append(channels[3])
        return ImageModule.merge(mode, out_channels)
    return image.point(lut)


def expand(image, border=0, fill=0):
    """Add a *border* pixel wide frame around the image."""
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
    new_w = w + left + right
    new_h = h + top + bottom

    if isinstance(fill, int):
        mode = image.mode
        if mode in ("RGB", "RGBA"):
            c = [fill, fill, fill] + ([255] if mode == "RGBA" else [])
        else:
            c = [fill]
    elif isinstance(fill, tuple):
        c = list(fill)
    else:
        c = [fill]

    out = ImageModule.new(image.mode, (new_w, new_h), c)
    out.paste(image, (left, top))
    return out


def crop(image, border=0):
    """Remove a *border* pixel wide frame from the image."""
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
    return image.crop((left, top, w - right, h - bottom))


def colorize(image, black, white, mid=None, blackpoint=0, whitepoint=255, midpoint=127):
    """Colorize a greyscale image.

    Map pixels at *blackpoint* to *black* colour, pixels at *whitepoint*
    to *white* colour, with optional *mid* colour at *midpoint*.
    """
    if image.mode != "L":
        image = image.convert("L")

    if isinstance(black, str):
        from PIL import ImageColor
        black = ImageColor.getrgb(black)
    if isinstance(white, str):
        from PIL import ImageColor
        white = ImageColor.getrgb(white)
    if mid is not None and isinstance(mid, str):
        from PIL import ImageColor
        mid = ImageColor.getrgb(mid)

    r_lut = []
    g_lut = []
    b_lut = []

    for i in range(256):
        if mid is None:
            # Linear interpolation black → white
            if whitepoint == blackpoint:
                t = 0.0
            else:
                t = max(0.0, min(1.0, (i - blackpoint) / (whitepoint - blackpoint)))
            r_lut.append(int(black[0] + (white[0] - black[0]) * t + 0.5))
            g_lut.append(int(black[1] + (white[1] - black[1]) * t + 0.5))
            b_lut.append(int(black[2] + (white[2] - black[2]) * t + 0.5))
        else:
            if i <= midpoint:
                if midpoint == blackpoint:
                    t = 0.0
                else:
                    t = max(0.0, min(1.0, (i - blackpoint) / (midpoint - blackpoint)))
                r_lut.append(int(black[0] + (mid[0] - black[0]) * t + 0.5))
                g_lut.append(int(black[1] + (mid[1] - black[1]) * t + 0.5))
                b_lut.append(int(black[2] + (mid[2] - black[2]) * t + 0.5))
            else:
                if whitepoint == midpoint:
                    t = 1.0
                else:
                    t = max(0.0, min(1.0, (i - midpoint) / (whitepoint - midpoint)))
                r_lut.append(int(mid[0] + (white[0] - mid[0]) * t + 0.5))
                g_lut.append(int(mid[1] + (white[1] - mid[1]) * t + 0.5))
                b_lut.append(int(mid[2] + (white[2] - mid[2]) * t + 0.5))

    # Clamp
    r_lut = [max(0, min(255, v)) for v in r_lut]
    g_lut = [max(0, min(255, v)) for v in g_lut]
    b_lut = [max(0, min(255, v)) for v in b_lut]

    # Apply LUTs to build RGB image
    r = image.point(r_lut)
    g = image.point(g_lut)
    b = image.point(b_lut)
    return ImageModule.merge("RGB", [r, g, b])


def exif_transpose(image):
    """Rotate/flip image according to EXIF orientation tag.

    Since we don't support EXIF metadata, this is a no-op that returns
    a copy of the image.
    """
    return image.copy()
