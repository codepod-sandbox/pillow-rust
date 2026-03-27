"""
Tests adapted from upstream Pillow test_imageops.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_imageops.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image, ImageOps
from helper import hopper, assert_image_equal


def test_sanity():
    """All ImageOps functions run without error — from upstream."""
    ImageOps.autocontrast(hopper("L"))
    ImageOps.autocontrast(hopper("RGB"))

    ImageOps.colorize(hopper("L"), (0, 0, 0), (255, 255, 255))
    ImageOps.colorize(hopper("L"), "black", "white")

    ImageOps.pad(hopper("L"), (128, 128))
    ImageOps.pad(hopper("RGB"), (128, 128))

    ImageOps.contain(hopper("L"), (128, 128))
    ImageOps.contain(hopper("RGB"), (128, 128))

    ImageOps.equalize(hopper("L"))
    ImageOps.equalize(hopper("RGB"))

    ImageOps.expand(hopper("L"), 1)
    ImageOps.expand(hopper("RGB"), 1)
    ImageOps.expand(hopper("L"), 2, 128)
    ImageOps.expand(hopper("RGB"), 2, (0, 0, 255))

    ImageOps.fit(hopper("L"), (128, 128))
    ImageOps.fit(hopper("RGB"), (128, 128))

    ImageOps.flip(hopper("L"))
    ImageOps.flip(hopper("RGB"))

    ImageOps.grayscale(hopper("L"))
    ImageOps.grayscale(hopper("RGB"))

    ImageOps.invert(hopper("L"))
    ImageOps.invert(hopper("RGB"))

    ImageOps.mirror(hopper("L"))
    ImageOps.mirror(hopper("RGB"))

    ImageOps.posterize(hopper("L"), 4)
    ImageOps.posterize(hopper("RGB"), 4)

    ImageOps.solarize(hopper("L"))
    ImageOps.solarize(hopper("RGB"))


def test_1pxfit():
    """Division by zero in fit if image is 1px — from upstream."""
    newimg = ImageOps.fit(hopper("RGB").resize((1, 1)), (35, 35))
    assert newimg.size == (35, 35)

    newimg = ImageOps.fit(hopper("RGB").resize((1, 100)), (35, 35))
    assert newimg.size == (35, 35)

    newimg = ImageOps.fit(hopper("RGB").resize((100, 1)), (35, 35))
    assert newimg.size == (35, 35)


def test_contain_various_sizes():
    """contain keeps aspect ratio — from upstream."""
    for new_size in ((256, 256), (512, 256), (256, 512)):
        im = hopper()
        new_im = ImageOps.contain(im, new_size)
        assert new_im.size[0] <= new_size[0]
        assert new_im.size[1] <= new_size[1]


def test_scale():
    """Test the scaling function — from upstream."""
    i = hopper("L").resize((50, 50))

    with pytest.raises(ValueError):
        ImageOps.scale(i, -1)

    newimg = ImageOps.scale(i, 1)
    assert newimg.size == (50, 50)

    newimg = ImageOps.scale(i, 2)
    assert newimg.size == (100, 100)

    newimg = ImageOps.scale(i, 0.5)
    assert newimg.size == (25, 25)


def test_invert_identity():
    """Double invert is identity — derived from upstream."""
    im = hopper("L")
    out = ImageOps.invert(ImageOps.invert(im))
    assert_image_equal(im, out)


def test_invert_identity_rgb():
    """Double invert is identity for RGB."""
    im = hopper("RGB")
    out = ImageOps.invert(ImageOps.invert(im))
    assert_image_equal(im, out)


def test_flip_flip_identity():
    """Double flip is identity — derived from upstream."""
    im = hopper("L")
    out = ImageOps.flip(ImageOps.flip(im))
    assert_image_equal(im, out)


def test_mirror_mirror_identity():
    """Double mirror is identity — derived from upstream."""
    im = hopper("L")
    out = ImageOps.mirror(ImageOps.mirror(im))
    assert_image_equal(im, out)


def test_expand():
    """expand adds border — derived from upstream."""
    im = hopper("L")
    expanded = ImageOps.expand(im, 10)
    assert expanded.size == (148, 148)

    expanded = ImageOps.expand(im, (1, 2, 3, 4))
    assert expanded.size == (132, 134)


def test_grayscale():
    """grayscale converts to L — from upstream sanity."""
    im = hopper("RGB")
    out = ImageOps.grayscale(im)
    assert out.mode == "L"
    assert out.size == im.size


def test_equalize():
    """equalize runs on small images — from upstream pil163."""
    i = hopper("RGB").resize((15, 16))
    ImageOps.equalize(i.convert("L"))
    ImageOps.equalize(i.convert("RGB"))


def test_pad_same_ratio():
    """Pad with same ratio doubles size — from upstream."""
    im = hopper()
    new_size = (im.width * 2, im.height * 2)
    new_im = ImageOps.pad(im, new_size)
    assert new_im.size == new_size


if __name__ == "__main__":
    pytest.main()
