"""
Tests adapted from upstream Pillow test_image.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# TestImage — core Image tests
# ---------------------------------------------------------------------------


def test_sanity():
    im = Image.new("L", (100, 100))
    assert im.mode == "L"
    assert im.size == (100, 100)

    im = Image.new("RGB", (100, 100))
    assert im.mode == "RGB"
    assert im.size == (100, 100)


def test_new_L_zero():
    im = Image.new("L", (100, 100), 0)
    data = im.getdata()
    assert all(v == 0 for v in data)


def test_width_height():
    im = Image.new("RGB", (1, 2))
    assert im.width == 1
    assert im.height == 2


def test_size_property():
    im = Image.new("RGB", (33, 44))
    assert im.size == (33, 44)


def test_comparison_with_other_type():
    item = Image.new("RGB", (25, 25), (0, 0, 0))
    num = 12
    assert item is not None
    assert item != num


def test_ne():
    im1 = Image.new("RGB", (25, 25), (0, 0, 0))
    im2 = Image.new("RGB", (25, 25), (255, 255, 255))
    assert im1 != im2


def test_eq_same():
    im1 = Image.new("RGB", (10, 10), (1, 2, 3))
    im2 = Image.new("RGB", (10, 10), (1, 2, 3))
    assert im1 == im2


def test_eq_different_mode():
    im1 = Image.new("RGB", (10, 10), (1, 2, 3))
    im2 = Image.new("L", (10, 10), 128)
    assert im1 != im2


def test_eq_different_size():
    im1 = Image.new("RGB", (10, 10), (1, 2, 3))
    im2 = Image.new("RGB", (20, 20), (1, 2, 3))
    assert im1 != im2


def test_getbands():
    assert Image.new("RGB", (1, 1)).getbands() == ("R", "G", "B")
    assert Image.new("RGBA", (1, 1)).getbands() == ("R", "G", "B", "A")
    assert Image.new("L", (1, 1)).getbands() == ("L",)
    assert Image.new("LA", (1, 1)).getbands() == ("L", "A")


def test_getbbox():
    # Non-zero image should return full bounding box
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    bbox = im.getbbox()
    assert bbox == (0, 0, 10, 10)


def test_getbbox_all_zero():
    im = Image.new("RGB", (10, 10), 0)
    bbox = im.getbbox()
    assert bbox is None


def test_getbbox_partial():
    im = Image.new("RGB", (10, 10), 0)
    im.putpixel((3, 4), (255, 0, 0))
    im.putpixel((7, 8), (0, 255, 0))
    bbox = im.getbbox()
    assert bbox == (3, 4, 8, 9)


def test_getchannel():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    r = im.getchannel(0)
    g = im.getchannel(1)
    b = im.getchannel(2)
    assert r.mode == "L"
    assert r.getpixel((0, 0)) == 10
    assert g.getpixel((0, 0)) == 20
    assert b.getpixel((0, 0)) == 30


def test_getchannel_by_name():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    r = im.getchannel("R")
    g = im.getchannel("G")
    b = im.getchannel("B")
    assert r.getpixel((0, 0)) == 10
    assert g.getpixel((0, 0)) == 20
    assert b.getpixel((0, 0)) == 30


def test_getchannel_wrong_params():
    im = Image.new("RGB", (10, 10))
    try:
        im.getchannel(-1)
        assert False, "should have raised"
    except ValueError:
        pass
    try:
        im.getchannel(3)
        assert False, "should have raised"
    except ValueError:
        pass
    try:
        im.getchannel("Z")
        assert False, "should have raised"
    except ValueError:
        pass


def test_close():
    im = Image.new("RGB", (10, 10))
    im.close()
    assert im._handle is None


def test_context_manager():
    with Image.new("RGB", (10, 10)) as im:
        assert im.size == (10, 10)


def test_repr():
    im = Image.new("RGB", (10, 20))
    r = repr(im)
    assert "RGB" in r
    assert "10x20" in r


def test_repr_closed():
    im = Image.new("RGB", (10, 10))
    im.close()
    assert "closed" in repr(im)


def test_color_name_black():
    im = Image.new("RGB", (1, 1), "black")
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_color_name_white():
    im = Image.new("RGB", (1, 1), "white")
    assert im.getpixel((0, 0)) == (255, 255, 255)


def test_color_name_red():
    im = Image.new("RGB", (1, 1), "red")
    assert im.getpixel((0, 0)) == (255, 0, 0)


def test_color_hex():
    im = Image.new("RGB", (1, 1), "#DDEEFF")
    assert im.getpixel((0, 0)) == (221, 238, 255)


def test_color_hex_short():
    im = Image.new("RGB", (1, 1), "#DEF")
    assert im.getpixel((0, 0)) == (221, 238, 255)


def test_check_size_list():
    """Image.new should accept lists too."""
    i = Image.new("RGB", [1, 1])
    assert isinstance(i.size, tuple)


def test_modes_constant():
    assert "RGB" in Image.MODES
    assert "RGBA" in Image.MODES
    assert "L" in Image.MODES
    assert "LA" in Image.MODES


def test_transpose_enum():
    assert Image.Transpose.FLIP_LEFT_RIGHT == 0
    assert Image.Transpose.FLIP_TOP_BOTTOM == 1
    assert Image.Transpose.ROTATE_90 == 2
    assert Image.Transpose.ROTATE_180 == 3
    assert Image.Transpose.ROTATE_270 == 4
    assert Image.Transpose.TRANSPOSE == 5
    assert Image.Transpose.TRANSVERSE == 6


def test_resampling_enum():
    assert Image.Resampling.NEAREST == "nearest"
    assert Image.Resampling.BILINEAR == "bilinear"
    assert Image.Resampling.BICUBIC == "bicubic"
    assert Image.Resampling.LANCZOS == "lanczos"


def test_getmodebands():
    assert Image.getmodebands("L") == 1
    assert Image.getmodebands("LA") == 2
    assert Image.getmodebands("RGB") == 3
    assert Image.getmodebands("RGBA") == 4


def test_info_attribute():
    im = Image.new("RGB", (10, 10))
    assert isinstance(im.info, dict)
    im.info["test_key"] = "test_value"
    assert im.info["test_key"] == "test_value"


def test_format_attribute():
    im = Image.new("RGB", (10, 10))
    assert im.format is None


def test_copy_preserves_info():
    im = Image.new("RGB", (10, 10))
    im.info["key"] = "value"
    out = im.copy()
    assert out.info["key"] == "value"
