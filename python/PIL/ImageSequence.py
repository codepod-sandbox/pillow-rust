"""PIL.ImageSequence — iterate over image frames."""


class Iterator:
    """Iterate over frames in an image sequence (GIF, APNG, etc.).

    For single-frame images, yields just the one frame.
    """

    def __init__(self, im):
        self.im = im
        self._pos = 0

    def __iter__(self):
        self._pos = 0
        return self

    def __next__(self):
        try:
            self.im.seek(self._pos)
        except EOFError:
            raise StopIteration
        self._pos += 1
        return self.im

    # Python 2 compat (some code still references this)
    next = __next__

    def __getitem__(self, ix):
        try:
            self.im.seek(ix)
        except EOFError:
            raise IndexError("frame index out of range")
        return self.im


def all_frames(im, func=None):
    """Return a list of all frames in the image, optionally applying func."""
    frames = []
    for frame in Iterator(im):
        if func:
            frames.append(func(frame.copy()))
        else:
            frames.append(frame.copy())
    return frames
