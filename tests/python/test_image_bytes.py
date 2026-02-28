"""
Tests adapted from upstream Pillow TestImageBytes + test_image_tobytes/getdata.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image.py
https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_tobytes.py
https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_getdata.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# frombytes roundtrip
# ---------------------------------------------------------------------------


def test_roundtrip_bytes_constructor_L():
    im = Image.new("L", (10, 10), 42)
    source_bytes = im.tobytes()
    reloaded = Image.frombytes("L", im.size, source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_constructor_RGB():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    source_bytes = im.tobytes()
    reloaded = Image.frombytes("RGB", im.size, source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_constructor_RGBA():
    im = Image.new("RGBA", (10, 10), (10, 20, 30, 40))
    source_bytes = im.tobytes()
    reloaded = Image.frombytes("RGBA", im.size, source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_constructor_LA():
    im = Image.new("LA", (10, 10), (128, 64))
    source_bytes = im.tobytes()
    reloaded = Image.frombytes("LA", im.size, source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_method_L():
    im = Image.new("L", (10, 10), 42)
    source_bytes = im.tobytes()
    reloaded = Image.new("L", im.size)
    reloaded.frombytes(source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_method_RGB():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    source_bytes = im.tobytes()
    reloaded = Image.new("RGB", im.size)
    reloaded.frombytes(source_bytes)
    assert reloaded.tobytes() == source_bytes


def test_roundtrip_bytes_method_RGBA():
    im = Image.new("RGBA", (10, 10), (10, 20, 30, 40))
    source_bytes = im.tobytes()
    reloaded = Image.new("RGBA", im.size)
    reloaded.frombytes(source_bytes)
    assert reloaded.tobytes() == source_bytes


# ---------------------------------------------------------------------------
# tobytes sanity
# ---------------------------------------------------------------------------


def test_tobytes_L():
    im = Image.new("L", (3, 2), 42)
    data = im.tobytes()
    assert isinstance(data, bytes)
    assert len(data) == 6  # 3*2*1


def test_tobytes_RGB():
    im = Image.new("RGB", (2, 2), (10, 20, 30))
    data = im.tobytes()
    assert len(data) == 12  # 2*2*3


def test_tobytes_RGBA():
    im = Image.new("RGBA", (2, 2), (10, 20, 30, 40))
    data = im.tobytes()
    assert len(data) == 16  # 2*2*4


# ---------------------------------------------------------------------------
# getdata
# ---------------------------------------------------------------------------


def test_getdata_L():
    im = Image.new("L", (3, 3), 42)
    data = im.getdata()
    assert len(data) == 9
    assert all(v == 42 for v in data)


def test_getdata_RGB():
    im = Image.new("RGB", (3, 3), (10, 20, 30))
    data = im.getdata()
    assert len(data) == 9
    assert all(v == (10, 20, 30) for v in data)


def test_getdata_RGBA():
    im = Image.new("RGBA", (2, 2), (10, 20, 30, 40))
    data = im.getdata()
    assert len(data) == 4
    assert all(v == (10, 20, 30, 40) for v in data)


# ---------------------------------------------------------------------------
# putdata
# ---------------------------------------------------------------------------


def test_putdata_L():
    im = Image.new("L", (3, 3))
    im.putdata([10, 20, 30, 40, 50, 60, 70, 80, 90])
    assert im.getpixel((0, 0)) == 10
    assert im.getpixel((2, 2)) == 90


def test_putdata_RGB():
    im = Image.new("RGB", (2, 2))
    im.putdata([(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)])
    assert im.getpixel((0, 0)) == (1, 2, 3)
    assert im.getpixel((1, 1)) == (10, 11, 12)


def test_putdata_roundtrip_L():
    im = Image.new("L", (10, 10), 42)
    data = im.getdata()
    im2 = Image.new("L", (10, 10))
    im2.putdata(data)
    assert_image_equal(im, im2)


def test_putdata_roundtrip_RGB():
    im = Image.new("RGB", (10, 10), (10, 20, 30))
    data = im.getdata()
    im2 = Image.new("RGB", (10, 10))
    im2.putdata(data)
    assert_image_equal(im, im2)
