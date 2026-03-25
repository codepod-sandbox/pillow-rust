"""
Tests adapted from upstream Pillow test_image.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
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


# ---------------------------------------------------------------------------
# Upstream tests — test_image.py (TestImage class)
# ---------------------------------------------------------------------------


def test_image_modes_success():
    """Upstream test_image_modes_success: supported modes should not raise."""
    for mode in Image.MODES:
        Image.new(mode, (1, 1))


def test_image_modes_fail():
    """Upstream test_image_modes_fail: bad modes raise ValueError."""
    for bad in ("", "bad", "very very long"):
        with pytest.raises((ValueError, Exception)):
            Image.new(bad, (1, 1))


def test_copy_is_independent():
    """Modifying a copy must not affect the original."""
    im = Image.new("RGB", (4, 4), (10, 20, 30))
    out = im.copy()
    out.putpixel((0, 0), (255, 0, 0))
    assert im.getpixel((0, 0)) == (10, 20, 30)
    assert out.getpixel((0, 0)) == (255, 0, 0)


def test_getcolors_simple():
    """getcolors() returns list of (count, color) pairs."""
    im = Image.new("RGB", (2, 2), (1, 2, 3))
    colors = im.getcolors()
    assert colors is not None
    assert len(colors) == 1
    count, color = colors[0]
    assert count == 4
    assert color == (1, 2, 3)


def test_getcolors_multiple():
    im = Image.new("L", (2, 2), 0)
    im.putpixel((1, 1), 255)
    colors = im.getcolors()
    assert colors is not None
    counts = {c: n for n, c in colors}
    assert counts[0] == 3
    assert counts[255] == 1


def test_getcolors_max_exceeded():
    """Returns None when unique colors exceed maxcolors."""
    im = Image.new("L", (256, 1))
    for x in range(256):
        im.putpixel((x, 0), x)
    # maxcolors=10 but there are 256 unique colours
    assert im.getcolors(maxcolors=10) is None


def test_getextrema_L():
    im = Image.new("L", (4, 4), 100)
    im.putpixel((0, 0), 10)
    im.putpixel((3, 3), 200)
    lo, hi = im.getextrema()
    assert lo == 10
    assert hi == 200


def test_getextrema_RGB():
    im = Image.new("RGB", (2, 2), (100, 100, 100))
    im.putpixel((0, 0), (0, 50, 200))
    extrema = im.getextrema()
    assert len(extrema) == 3
    r_lo, r_hi = extrema[0]
    g_lo, g_hi = extrema[1]
    b_lo, b_hi = extrema[2]
    assert r_lo == 0 and r_hi == 100
    assert g_lo == 50 and g_hi == 100
    assert b_lo == 100 and b_hi == 200


def test_histogram_L():
    """histogram() for L image: list of 256 ints."""
    im = Image.new("L", (2, 2), 0)
    im.putpixel((1, 1), 255)
    hist = im.histogram()
    assert len(hist) == 256
    assert hist[0] == 3
    assert hist[255] == 1
    assert sum(hist) == 4


def test_histogram_RGB():
    """histogram() for RGB image: list of 256*3 ints."""
    im = Image.new("RGB", (1, 1), (10, 20, 30))
    hist = im.histogram()
    assert len(hist) == 768
    # R channel
    assert hist[10] == 1
    # G channel
    assert hist[256 + 20] == 1
    # B channel
    assert hist[512 + 30] == 1


def test_split_merge_roundtrip():
    """split() then merge() should produce an identical image."""
    im = Image.new("RGB", (10, 10), (50, 100, 150))
    r, g, b = im.split()
    merged = Image.merge("RGB", [r, g, b])
    assert merged.tobytes() == im.tobytes()


def test_split_merge_RGBA():
    im = Image.new("RGBA", (4, 4), (10, 20, 30, 200))
    channels = im.split()
    assert len(channels) == 4
    back = Image.merge("RGBA", list(channels))
    assert back.tobytes() == im.tobytes()


def test_putalpha_int():
    """putalpha(int) sets alpha channel to a constant."""
    im = Image.new("RGBA", (4, 4), (100, 100, 100, 255))
    im.putalpha(128)
    assert im.getpixel((0, 0))[3] == 128
    assert im.getpixel((3, 3))[3] == 128


def test_putalpha_image():
    """putalpha(L image) sets per-pixel alpha values."""
    im = Image.new("RGBA", (2, 2), (100, 100, 100, 255))
    mask = Image.new("L", (2, 2), 0)
    mask.putpixel((1, 1), 200)
    im.putalpha(mask)
    assert im.getpixel((0, 0))[3] == 0
    assert im.getpixel((1, 1))[3] == 200


def test_point_lut_list():
    """point() with a 256-element list applies the LUT."""
    im = Image.new("L", (4, 4), 100)
    lut = [255 - i for i in range(256)]
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 155   # 255 - 100


def test_point_lambda():
    """point() with a callable applies the function per-pixel."""
    im = Image.new("L", (4, 4), 50)
    out = im.point(lambda v: v * 2)
    assert out.getpixel((0, 0)) == 100


def test_getdata_putdata_roundtrip():
    """getdata() then putdata() reproduces the original image."""
    im = Image.new("RGB", (3, 3), (10, 20, 30))
    data = im.getdata()
    im2 = Image.new("RGB", (3, 3))
    im2.putdata(data)
    assert im.tobytes() == im2.tobytes()


def test_frombytes():
    """frombytes() loads raw pixel data correctly."""
    im = Image.new("RGB", (2, 2), (1, 2, 3))
    raw = im.tobytes()
    im2 = Image.frombytes("RGB", (2, 2), raw)
    assert im2.tobytes() == raw


def test_open_save_roundtrip(tmp_path):
    """open() then save() roundtrips PNG pixel-perfectly."""
    im = Image.new("RGB", (10, 10), (77, 88, 99))
    path = str(tmp_path / "test.png")
    im.save(path)
    im2 = Image.open(path)
    assert im2.size == (10, 10)
    assert im2.getpixel((0, 0)) == (77, 88, 99)


# ---------------------------------------------------------------------------
# alpha_composite
# ---------------------------------------------------------------------------

def test_alpha_composite_opaque_src():
    """Opaque src replaces dst completely."""
    dst = Image.new("RGBA", (2, 2), (0, 0, 255, 255))
    src = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    out = Image.alpha_composite(dst, src)
    assert out.getpixel((0, 0)) == (255, 0, 0, 255)


def test_alpha_composite_transparent_src():
    """Fully transparent src leaves dst unchanged."""
    dst = Image.new("RGBA", (2, 2), (0, 0, 255, 200))
    src = Image.new("RGBA", (2, 2), (255, 0, 0, 0))
    out = Image.alpha_composite(dst, src)
    px = out.getpixel((0, 0))
    assert px == (0, 0, 255, 200)


def test_alpha_composite_returns_new_image():
    """alpha_composite does not modify dst in place."""
    dst = Image.new("RGBA", (2, 2), (0, 0, 255, 255))
    src = Image.new("RGBA", (2, 2), (255, 0, 0, 128))
    original_bytes = dst.tobytes()
    out = Image.alpha_composite(dst, src)
    assert dst.tobytes() == original_bytes
    assert out is not dst


def test_alpha_composite_requires_rgba():
    """alpha_composite raises for non-RGBA images."""
    dst = Image.new("RGB", (2, 2))
    src = Image.new("RGBA", (2, 2))
    with pytest.raises(ValueError):
        Image.alpha_composite(dst, src)


def test_alpha_composite_instance_method():
    """Image.alpha_composite(src) instance form works."""
    dst = Image.new("RGBA", (10, 10), (0, 0, 255, 255))
    src = Image.new("RGBA", (5, 5), (255, 0, 0, 255))
    dst.alpha_composite(src, dest=(2, 2))
    assert dst.getpixel((2, 2)) == (255, 0, 0, 255)
    assert dst.getpixel((0, 0)) == (0, 0, 255, 255)


def test_alpha_composite_half_alpha():
    """50% alpha src blends with dst."""
    dst = Image.new("RGBA", (2, 2), (0, 0, 0, 255))
    src = Image.new("RGBA", (2, 2), (200, 0, 0, 128))
    out = Image.alpha_composite(dst, src)
    px = out.getpixel((0, 0))
    # Result should be reddish with full alpha
    assert px[3] == 255
    assert px[0] > 50  # some red blended in
