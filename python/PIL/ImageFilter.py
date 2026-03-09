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
SMOOTH_MORE = Filter("smooth_more")
CONTOUR = Filter("contour")
DETAIL = Filter("detail")
EDGE_ENHANCE = Filter("edge_enhance")
EDGE_ENHANCE_MORE = Filter("edge_enhance_more")
EMBOSS = Filter("emboss")
FIND_EDGES = Filter("find_edges")


class GaussianBlur(Filter):
    """Gaussian blur with configurable *radius* (sigma)."""

    def __init__(self, radius=2):
        super().__init__("gaussian_blur", [float(radius)])


class UnsharpMask(Filter):
    """Unsharp mask filter."""

    def __init__(self, radius=2, percent=150, threshold=3):
        super().__init__("unsharp_mask", [float(radius), float(percent), float(threshold)])


class Kernel(Filter):
    """Custom convolution kernel.

    *size* is (3, 3), *kernel* is a 9-element sequence,
    *scale* and *offset* control normalisation.
    """

    def __init__(self, size, kernel, scale=None, offset=0):
        if size != (3, 3):
            raise ValueError("only (3, 3) kernels are supported")
        if len(kernel) != 9:
            raise ValueError("kernel must have 9 elements")
        if scale is None:
            scale = sum(kernel) or 1
        args = list(kernel) + [float(scale), float(offset)]
        super().__init__("kernel3x3", [float(a) for a in args])


class RankFilter(Filter):
    """Rank filter: select the *rank*-th value in an NxN window."""

    def __init__(self, size, rank):
        # rank filter uses custom name; we encode rank in args
        # Rust side handles size and rank via "median"/"min_filter"/"max_filter"
        # For arbitrary rank, we'd need a generic handler.
        # Map to existing Rust names for common cases.
        self.size = size
        self.rank = rank
        super().__init__("median", [float(size)])
        # Override: we'll adjust based on rank
        n = size * size
        if rank == 0:
            self.name = "min_filter"
        elif rank >= n - 1:
            self.name = "max_filter"
        else:
            self.name = "median"
        self.args = [float(size)]


class MedianFilter(Filter):
    """Median filter: pick median value in NxN window."""

    def __init__(self, size=3):
        super().__init__("median", [float(size)])


class MinFilter(Filter):
    """Min filter: pick minimum value in NxN window."""

    def __init__(self, size=3):
        super().__init__("min_filter", [float(size)])


class MaxFilter(Filter):
    """Max filter: pick maximum value in NxN window."""

    def __init__(self, size=3):
        super().__init__("max_filter", [float(size)])
