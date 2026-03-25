"""PIL.ImagePath — 2D vector geometry."""

class Path:
    """A 2D path of (x, y) points."""

    def __init__(self, xy=None):
        if xy is None:
            self._coords = []
        elif isinstance(xy, Path):
            self._coords = list(xy._coords)
        else:
            # Accept flat list [x0,y0,x1,y1,...] or list of tuples [(x0,y0),...]
            coords = list(xy)
            if coords and not isinstance(coords[0], (list, tuple)):
                # Flat list
                self._coords = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
            else:
                self._coords = [(float(p[0]), float(p[1])) for p in coords]

    def tolist(self, flat=0):
        """Return coordinates as a list.
        If flat is true, return [x0, y0, x1, y1, ...].
        Otherwise return [(x0, y0), (x1, y1), ...].
        """
        if flat:
            result = []
            for x, y in self._coords:
                result.append(x)
                result.append(y)
            return result
        return list(self._coords)

    def getbbox(self):
        """Return bounding box as (x0, y0, x1, y1)."""
        if not self._coords:
            return None
        xs = [p[0] for p in self._coords]
        ys = [p[1] for p in self._coords]
        return (min(xs), min(ys), max(xs), max(ys))

    def compact(self, distance=2):
        """Remove points closer than *distance* to each other.
        Returns the number of points removed."""
        if len(self._coords) < 2:
            return 0
        d2 = distance * distance
        original_len = len(self._coords)
        result = [self._coords[0]]
        for p in self._coords[1:]:
            dx = p[0] - result[-1][0]
            dy = p[1] - result[-1][1]
            if dx * dx + dy * dy >= d2:
                result.append(p)
        self._coords = result
        return original_len - len(self._coords)

    def map(self, func):
        """Apply *func* to each point."""
        self._coords = [func(x, y) for x, y in self._coords]

    def transform(self, matrix):
        """Apply an affine transform (6-element tuple)."""
        a, b, c, d, e, f = matrix
        self._coords = [
            (a * x + b * y + c, d * x + e * y + f) for x, y in self._coords
        ]

    def __len__(self):
        return len(self._coords)

    def __getitem__(self, index):
        return self._coords[index]

    def __repr__(self):
        return f"Path({self._coords!r})"
