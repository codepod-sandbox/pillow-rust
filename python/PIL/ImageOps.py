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
    return Image(_pil_native.image_invert(image._handle))


def autocontrast(image, cutoff=0, ignore=None):
    """Maximize image contrast by stretching the histogram."""
    return Image(_pil_native.image_autocontrast(image._handle))


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
    w, h = image.size
    new_w = max(1, int(w * factor))
    new_h = max(1, int(h * factor))
    if resample is not None:
        return image.resize((new_w, new_h), resample=resample)
    return image.resize((new_w, new_h))
