"""
PIL.ImageFilter — predefined image filters.
"""


class Filter:
    """Base filter descriptor passed to Image.filter()."""

    def __init__(self, name, args=None):
        self.name = name
        self.args = args


BLUR = Filter("blur")
SHARPEN = Filter("sharpen")
SMOOTH = Filter("smooth")


class GaussianBlur(Filter):
    """Gaussian blur with configurable *radius* (sigma)."""

    def __init__(self, radius=2):
        super().__init__("gaussian_blur", [float(radius)])
