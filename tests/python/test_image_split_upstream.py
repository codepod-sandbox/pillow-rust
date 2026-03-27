"""
Tests adapted from upstream Pillow test_image_split.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_split.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_split():
    def split(mode):
        layers = hopper(mode).split()
        return [(i.mode, i.size[0], i.size[1]) for i in layers]

    assert split("L") == [("L", 128, 128)]
    assert split("RGB") == [("L", 128, 128), ("L", 128, 128), ("L", 128, 128)]
    assert split("RGBA") == [
        ("L", 128, 128),
        ("L", 128, 128),
        ("L", 128, 128),
        ("L", 128, 128),
    ]


@pytest.mark.parametrize("mode", ("L", "RGB", "RGBA"))
def test_split_merge(mode):
    """Split then merge should produce the original image."""
    expected = Image.merge(mode, hopper(mode).split())
    assert_image_equal(hopper(mode), expected)


def test_split_open():
    """Split an image that was saved and reopened."""
    import tempfile, os
    test_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    try:
        def split_open(mode):
            hopper(mode).save(test_file)
            with Image.open(test_file) as im:
                return len(im.split())

        assert split_open("L") == 1
        assert split_open("RGB") == 3
        assert split_open("RGBA") == 4
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    pytest.main()
