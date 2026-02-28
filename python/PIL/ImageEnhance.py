"""
PIL.ImageEnhance — image enhancement classes.
"""

import _pil_native
from PIL.Image import Image


class _Enhancer:
    """Base class for image enhancers."""

    def __init__(self, image):
        self._image = image
        self._kind = ""

    def enhance(self, factor):
        """Return an enhanced copy. factor=1.0 returns original."""
        new_handle = _pil_native.image_enhance(
            self._image._handle, self._kind, float(factor)
        )
        return Image(new_handle)


class Brightness(_Enhancer):
    """Adjust image brightness. factor=0.0 is black, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "brightness"


class Contrast(_Enhancer):
    """Adjust image contrast. factor=0.0 is solid gray, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "contrast"


class Color(_Enhancer):
    """Adjust color saturation. factor=0.0 is grayscale, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "color"


class Sharpness(_Enhancer):
    """Adjust image sharpness. factor=0.0 is blurred, 1.0 is original, 2.0 is sharpened."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "sharpness"
