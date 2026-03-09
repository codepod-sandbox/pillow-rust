"""
PIL.ImageEnhance — image enhancement classes.
"""

import _pil_native
from PIL.Image import Image


class _Enhance:
    """Base class for enhancers."""

    def enhance(self, factor):
        """Return enhanced image. factor=1.0 returns original."""
        raise NotImplementedError


class Brightness(_Enhance):
    """Adjust image brightness.

    factor=0.0 gives black, 1.0 gives original, >1.0 brightens.
    """

    def __init__(self, image):
        self._image = image

    def enhance(self, factor):
        return Image(_pil_native.image_adjust_brightness(self._image._handle, float(factor)))


class Contrast(_Enhance):
    """Adjust image contrast.

    factor=0.0 gives solid grey, 1.0 gives original, >1.0 increases contrast.
    """

    def __init__(self, image):
        self._image = image

    def enhance(self, factor):
        return Image(_pil_native.image_adjust_contrast(self._image._handle, float(factor)))


class Color(_Enhance):
    """Adjust colour saturation.

    factor=0.0 gives greyscale, 1.0 gives original, >1.0 increases saturation.
    """

    def __init__(self, image):
        self._image = image

    def enhance(self, factor):
        return Image(_pil_native.image_adjust_color(self._image._handle, float(factor)))


class Sharpness(_Enhance):
    """Adjust image sharpness.

    factor=0.0 gives blurred, 1.0 gives original, >1.0 sharpens.
    """

    def __init__(self, image):
        self._image = image

    def enhance(self, factor):
        return Image(_pil_native.image_adjust_sharpness(self._image._handle, float(factor)))
