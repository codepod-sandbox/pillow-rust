# Design: PyO3 `_imaging` Module — Pillow Drop-in Replacement

**Date:** 2026-04-13  
**Status:** Approved

## Goal

Replace the RustPython-based `_pil_native` binding and our custom `python/PIL/` layer with a PyO3 extension module named `_imaging` that is compatible with Pillow's real C extension. Pair it with upstream Pillow Python files to make pillow-rust a true drop-in replacement.

## Motivation

The current architecture has two problems:
1. We maintain our own Python wrappers (`python/PIL/*.py`) that diverge from upstream Pillow, requiring manual test porting.
2. The RustPython binding (`_pil_native`) uses a handle-based design that doesn't match Pillow's object-based `_imaging` API.

Switching to PyO3 + upstream Python files means: upstream tests run directly, API compatibility is verified against the real thing, and Pillow version upgrades are a file copy.

When the PyO3-RustPython backend matures, RustPython compatibility comes for free.

## Approach

**Approach B:** Implement `_imaging` as a PyO3 extension with the full in-memory API. Override `Image.open()` and `Image.save()` in `Image.py` with a Rust-native fast path using the `image` crate. Skip the streaming codec interface entirely.

## Repository Changes

### Deleted
- `crates/pil-rust-python/` — RustPython `_pil_native` bindings
- `tests/python/` — 1900+ adapted tests, pytest shim, `run_all.py`
- The `pil-python` RustPython binary target

### New
- `crates/pil-imaging/` — PyO3 crate producing `_imaging.so` / `_imaging.pyd`

### Replaced
- `python/PIL/` — upstream Pillow Python files verbatim, with two patches to `Image.py`

### Unchanged
- `crates/pil-rust-core/` — all image operations in pure Rust
- `crates/pil-rust-wasm/` — WASM target

## `crates/pil-imaging/` Crate

```toml
[lib]
name = "_imaging"
crate-type = ["cdylib"]

[dependencies]
pil-rust-core = { path = "../pil-rust-core" }
pyo3 = { version = "0.22", features = ["extension-module"] }
```

Built with `maturin`. Output placed in `python/PIL/_imaging.so`.

## `_imaging` Module API

### `ImagingCore` class (`#[pyclass]`)

Wraps `pil-rust-core::ImageHandle`. Implements all ~65 methods that upstream `Image.py` calls on `self.im`:

**Pixel access:**
`getpixel(xy)`, `putpixel(xy, color)`, `pixel_access(readonly) → PixelAccess`

**Properties:**
`size`, `mode`, `bands`, `readonly`

**Geometry:**
`resize(size, filter)`, `crop(box)`, `rotate(angle, ...)`, `transpose(method)`, `transform(size, method, data, ...)`, `reduce(factor, box)`, `offset(xoffset, yoffset)`, `expand(x, y, color)`

**Color:**
`convert(mode)`, `convert2(mode, ...)`, `convert_matrix(mode, matrix)`, `convert_transparent(mode, color)`, `point(lut, mode)`, `point_transform(scale, offset)`, `setmode(mode)`

**Channel:**
`split() → list[ImagingCore]`, `getband(n) → ImagingCore`, `putband(im, n)`, `fillband(n, value)`

**Statistics:**
`histogram(mask, extrema)`, `getbbox()`, `getextrema()`, `getcolors(maxcolors)`, `getprojection()`, `entropy(mask, extrema)`

**Filters:**
`filter(name, args)`, `gaussian_blur(radius)`, `box_blur(radius, n)`, `unsharp_mask(radius, percent, threshold)`, `rankfilter(size, rank)`, `modefilter(size)`

**Compositing:**
`paste(im, box, mask)`, `alpha_composite(im, dest, source)`

**Chops (ImageChops operations — all operate on two ImagingCore objects):**
`chop_add`, `chop_add_modulo`, `chop_subtract`, `chop_subtract_modulo`, `chop_multiply`, `chop_screen`, `chop_difference`, `chop_darker`, `chop_lighter`, `chop_invert`, `chop_and`, `chop_or`, `chop_xor`, `chop_soft_light`, `chop_hard_light`, `chop_overlay`

**Misc:**
`copy()`, `quantize(colors)`, `putdata(data, scale, offset)`, `color_lut_3d(...)`, `effect_spread(distance)`, `save_ppm(fp)`, `ptr` (raw pointer for numpy), `isblock()`

**Palette (stubbed — raise ValueError for unsupported modes):**
`getpalette()`, `getpalettemode()`, `putpalette()`, `putpalettealpha()`, `putpalettealphas()`

### `ImagingDraw` class (`#[pyclass]`)

Returned by `_imaging.draw(im)`. Used by upstream `ImageDraw.py` for low-level drawing. Methods map to our existing `pil-rust-core` draw functions:

`draw_arc`, `draw_chord`, `draw_ellipse`, `draw_lines`, `draw_outline`, `draw_pieslice`, `draw_points`, `draw_polygon`, `draw_rectangle`, `draw_bitmap`, `draw_ink`

### `Font` class (`#[pyclass]`)

Returned by `_imaging.font(image_im, data)` for bitmap fonts. Wraps our existing `FontHandle`. Methods:

`render(text, fill, mode, dir, features, lang, stroke_width, anchor, ink, start)` → renders text into `ImagingCore`  
`getsize(text, ...)` → `(width, height)`  
`getlength(text, ...)` → `float`  
`ascent`, `descent`, `height`, `x_ppem`, `y_ppem` (properties)  
`family`, `style`, `glyphs` (properties — stub with empty values for bitmap fonts)  
`getvarnames`, `getvaraxes`, `setvarname`, `setvaraxes` (variable font stubs — raise `NotImplementedError`)

### `ImagingPath` class (`#[pyclass]`)

Returned by `_imaging.path(coords)`. Used by `ImagePath.py`. Wraps a `Vec<(f32, f32)>`. Methods:

`tolist(flat=False)` → list of coords  
`getbbox()` → `(x0, y0, x1, y1)`  
`transform(matrix)` → applies affine transform in-place  
`compact(distance)` → removes points closer than `distance`  
`map(func)` → applies Python function to each point  
`id` (property) — internal pointer id

### `PixelAccess` class (`#[pyclass]`)

Holds a reference to `ImagingCore`. Supports `__getitem__((x, y))` and `__setitem__((x, y), color)`.

### Module-level functions

| Function | Notes |
|---|---|
| `new(mode, size) → ImagingCore` | |
| `merge(mode, *bands) → ImagingCore` | varargs of ImagingCore |
| `blend(im1, im2, alpha) → ImagingCore` | |
| `alpha_composite(dst, src)` | in-place |
| `fill(mode, size, color) → ImagingCore` | |
| `linear_gradient(mode) → ImagingCore` | |
| `radial_gradient(mode) → ImagingCore` | |
| `draw(im) → ImagingDraw` | see ImagingDraw class below |
| `font(image_im, data) → Font` | bitmap font; see Font class below |
| `path(coords) → ImagingPath` | see ImagingPath class below |
| `open_from_bytes(data: bytes) → ImagingCore` | **NEW** — Rust-native decode |
| `save_to_bytes(im, format, **opts) → bytes` | **NEW** — Rust-native encode |
| `new_block(mode, size)`, `clear_cache()`, `set_alignment(n)`, etc. | memory management stubs (no-ops) |
| `get_stats()`, `reset_stats()` | diagnostic stubs |
| All codec factories (`jpeg_decoder`, `raw_decoder`, etc.) | raise `NotImplementedError` |

### Constants

```python
PILLOW_VERSION = "12.1.1"  # tracks upstream version being copied
DEFAULT_STRATEGY = 0
FILTERED = 1
HUFFMAN_ONLY = 2
RLE = 3
FIXED = 4
HAVE_LIBIMAGEQUANT = False
HAVE_LIBJPEGTURBO = False
HAVE_MOZJPEG = False
HAVE_XCB = False
HAVE_ZLIBNG = False
jpeglib_version = ""
libtiff_version = ""
zlib_version = ""
zlib_ng_version = ""
libjpeg_turbo_version = ""
jp2klib_version = ""
```

## `Image.py` Patches

Two early-exit fast paths, clearly marked, leaving all original logic intact for fallback.

### `Image.open()` patch

```python
def open(fp, mode="r", formats=None):
    # --- pillow-rust fast path ---
    if is_path(fp):
        with builtins.open(os.fspath(fp), "rb") as f:
            data = f.read()
        im = Image()
        im._im = core.open_from_bytes(data)
        im._mode = im._im.mode
        im._size = im._im.size
        return im
    # --- original Pillow logic follows unchanged ---
```

### `Image.save()` patch

```python
def save(self, fp, format=None, **params):
    # --- pillow-rust fast path ---
    if is_path(fp):
        fmt = (format or os.path.splitext(os.fspath(fp))[1][1:]).upper()
        data = core.save_to_bytes(self.im, fmt, **params)
        with builtins.open(os.fspath(fp), "wb") as f:
            f.write(data)
        return
    # --- original Pillow logic follows unchanged ---
```

File-like objects (`BytesIO` etc.) fall through to original Pillow logic and will raise errors for unsupported codecs — acceptable for now.

## Supported File Formats

Via the `image` crate: JPEG, PNG, BMP, GIF (decode only), TIFF, WebP, ICO, TGA, PPM.  
Unsupported: PSD, XCF, PCX, FLI, JPEG2000, and other niche formats.

## Unsupported Features

These raise `ValueError` or `NotImplementedError`:
- Mode `P` (palette), `CMYK`, `I`, `F`, `1`, `YCbCr`, `LAB`, `HSV`
- `Image.frombuffer()` with codec pipeline
- Animation frames (`seek`, `tell`, `n_frames`)
- EXIF, ICC profiles, image metadata
- `ImageCms` (color management)
- Screen capture (`grabscreen_x11`)

## Testing

- Copy upstream Pillow `Tests/` directory
- Run with real `pytest`: `pytest Tests/test_image.py Tests/test_imageops.py ...`
- Skip tests requiring unsupported formats via `pytest.mark.skip` or `-k` filtering
- No custom test shim needed

## Migration Sequence

1. Add `crates/pil-imaging/` with PyO3 skeleton — `ImagingCore` wrapping `ImageHandle`
2. Implement all `ImagingCore` methods
3. Implement module-level functions
4. Copy upstream Pillow Python files to `python/PIL/`
5. Apply two `Image.py` patches
6. Run upstream tests, fix gaps
7. Delete `crates/pil-rust-python/`, `tests/python/`, binary target
