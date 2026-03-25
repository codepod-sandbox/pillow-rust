"""
PIL.ImageStat — image statistics.
"""

import math


class Stat:
    """Calculate statistics for the given image (or image + mask).

    Properties: extrema, count, sum, sum2, mean, median, rms, var, stddev.
    """

    def __init__(self, image_or_list, mask=None):
        if isinstance(image_or_list, list):
            self.h = image_or_list
        elif hasattr(image_or_list, "histogram"):
            self.h = image_or_list.histogram(mask)
        else:
            raise TypeError(f"expected image or list, got {type(image_or_list).__name__}")

        # Determine number of bands
        if len(self.h) == 256:
            self.bands = 1
        elif len(self.h) == 768:
            self.bands = 3
        elif len(self.h) == 1024:
            self.bands = 4
        else:
            self.bands = len(self.h) // 256 if len(self.h) % 256 == 0 else 1

    def _get_band(self, band):
        return self.h[band * 256 : (band + 1) * 256]

    @property
    def extrema(self):
        """Min and max for each band as list of (min, max) tuples."""
        result = []
        for b in range(self.bands):
            h = self._get_band(b)
            lo = hi = None
            for i in range(256):
                if h[i]:
                    if lo is None:
                        lo = i
                    hi = i
            if lo is None:
                result.append((0, 0))
            else:
                result.append((lo, hi))
        return result

    @property
    def count(self):
        """Pixel count per band."""
        return [sum(self._get_band(b)) for b in range(self.bands)]

    @property
    def sum(self):
        """Sum of pixel values per band."""
        result = []
        for b in range(self.bands):
            h = self._get_band(b)
            result.append(sum(i * h[i] for i in range(256)))
        return result

    @property
    def sum2(self):
        """Sum of squared pixel values per band."""
        result = []
        for b in range(self.bands):
            h = self._get_band(b)
            result.append(sum(i * i * h[i] for i in range(256)))
        return result

    @property
    def mean(self):
        """Mean pixel value per band."""
        s = self.sum
        c = self.count
        return [s[b] / c[b] if c[b] else 0.0 for b in range(self.bands)]

    @property
    def median(self):
        """Median pixel value per band."""
        result = []
        for b in range(self.bands):
            h = self._get_band(b)
            total = sum(h)
            if total == 0:
                result.append(0)
                continue
            half = total // 2
            cumulative = 0
            for i in range(256):
                cumulative += h[i]
                if cumulative > half:
                    result.append(i)
                    break
            else:
                result.append(255)
        return result

    @property
    def rms(self):
        """Root mean square per band."""
        s2 = self.sum2
        c = self.count
        return [math.sqrt(s2[b] / c[b]) if c[b] else 0.0 for b in range(self.bands)]

    @property
    def var(self):
        """Variance per band."""
        s = self.sum
        s2 = self.sum2
        c = self.count
        result = []
        for b in range(self.bands):
            if c[b] == 0:
                result.append(0.0)
            else:
                m = s[b] / c[b]
                result.append(s2[b] / c[b] - m * m)
        return result

    @property
    def stddev(self):
        """Standard deviation per band."""
        return [math.sqrt(v) for v in self.var]
