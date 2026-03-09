"""
PIL.ImageChops — channel operations (arithmetic on images).
"""

from PIL import Image as ImageModule
from PIL.Image import Image


def add(image1, image2, scale=1.0, offset=0):
    """Add two images: out = (image1 + image2) / scale + offset."""
    return _binop(image1, image2, lambda a, b: int((a + b) / scale + offset))


def add_modulo(image1, image2):
    """Add two images without clipping: out = (image1 + image2) % 256."""
    return _binop(image1, image2, lambda a, b: (a + b) % 256)


def subtract(image1, image2, scale=1.0, offset=0):
    """Subtract two images: out = (image1 - image2) / scale + offset."""
    return _binop(image1, image2, lambda a, b: int((a - b) / scale + offset))


def subtract_modulo(image1, image2):
    """Subtract two images without clipping: out = (image1 - image2) % 256."""
    return _binop(image1, image2, lambda a, b: (a - b) % 256)


def multiply(image1, image2):
    """Multiply two images: out = image1 * image2 / 255."""
    return _binop(image1, image2, lambda a, b: (a * b) // 255)


def screen(image1, image2):
    """Screen blend: out = 255 - ((255 - image1) * (255 - image2) / 255)."""
    return _binop(image1, image2, lambda a, b: 255 - ((255 - a) * (255 - b) // 255))


def soft_light(image1, image2):
    """Soft light blend."""
    def op(a, b):
        t = a * b / 255.0
        return int(t + a * (255 - (255 - a) * (255 - b) / 255.0 - t) / 255.0)
    return _binop(image1, image2, op)


def hard_light(image1, image2):
    """Hard light blend."""
    def op(a, b):
        if b < 128:
            return (2 * a * b) // 255
        else:
            return 255 - (2 * (255 - a) * (255 - b)) // 255
    return _binop(image1, image2, op)


def overlay(image1, image2):
    """Overlay blend (hard light with swapped inputs)."""
    return hard_light(image2, image1)


def darker(image1, image2):
    """Select darker pixel: out = min(image1, image2)."""
    return _binop(image1, image2, lambda a, b: min(a, b))


def lighter(image1, image2):
    """Select lighter pixel: out = max(image1, image2)."""
    return _binop(image1, image2, lambda a, b: max(a, b))


def difference(image1, image2):
    """Absolute difference: out = abs(image1 - image2)."""
    return _binop(image1, image2, lambda a, b: abs(a - b))


def invert(image):
    """Invert image: out = 255 - image."""
    lut = [255 - i for i in range(256)]
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


def constant(image, value):
    """Return L-mode image filled with a constant *value*, same size as input."""
    return ImageModule.new("L", image.size, value)


def duplicate(image):
    """Return a copy of the image."""
    return image.copy()


def offset(image, xoffset, yoffset=None):
    """Offset image data. Wraps around edges."""
    if yoffset is None:
        yoffset = xoffset
    w, h = image.size
    xoffset = xoffset % w
    yoffset = yoffset % h
    # Crop four quadrants and reassemble
    parts = [
        (image.crop((w - xoffset, h - yoffset, w, h)), (0, 0)),
        (image.crop((0, h - yoffset, w - xoffset, h)), (xoffset, 0)),
        (image.crop((w - xoffset, 0, w, h - yoffset)), (0, yoffset)),
        (image.crop((0, 0, w - xoffset, h - yoffset)), (xoffset, yoffset)),
    ]
    out = ImageModule.new(image.mode, image.size)
    for piece, pos in parts:
        out.paste(piece, pos)
    return out


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _binop(im1, im2, func):
    """Apply a per-channel binary operation to two images."""
    mode = im1.mode
    w, h = im1.size

    if mode == "L":
        d1 = im1.getdata()
        d2 = im2.getdata()
        out_data = [max(0, min(255, func(a, b))) for a, b in zip(d1, d2)]
        out = ImageModule.new("L", (w, h))
        out.putdata(out_data)
        return out

    # RGB or RGBA
    channels1 = im1.split()
    channels2 = im2.split()
    bands = min(len(channels1), len(channels2))
    # Only operate on colour channels (not alpha)
    color_bands = 3 if bands >= 3 else bands

    out_channels = []
    for i in range(color_bands):
        d1 = channels1[i].getdata()
        d2 = channels2[i].getdata()
        out_data = [max(0, min(255, func(a, b))) for a, b in zip(d1, d2)]
        ch = ImageModule.new("L", (w, h))
        ch.putdata(out_data)
        out_channels.append(ch)

    # Preserve alpha from first image
    if mode == "RGBA" and len(channels1) >= 4:
        out_channels.append(channels1[3])

    return ImageModule.merge(mode, out_channels)
