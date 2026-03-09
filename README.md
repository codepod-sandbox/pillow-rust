# pillow-rust

A Rust-backed implementation of Python's [Pillow](https://pillow.readthedocs.io/) imaging library, designed to run in WASM via [RustPython](https://github.com/RustPython/RustPython). Part of the [Codepod](https://github.com/codepod-sandbox/codepod) sandbox.

## Why

LLMs frequently generate code that uses Pillow. This provides a compatible subset that runs entirely in a WASM sandbox — no native dependencies, no filesystem access required for core operations.

## Architecture

```
Python code (from PIL import Image)
        │
        ▼
  PIL/*.py          ← Pillow-compatible Python API (12 modules)
        │
        ▼
  pil-rust-python   ← RustPython bindings (#[pymodule] _pil_native)
        │
        ▼
  pil-rust-core     ← Pure Rust image operations (wraps `image` crate)
```

**pil-rust-core** handles all image manipulation using the [`image`](https://docs.rs/image) crate. Images are stored in a thread-local handle table — Python holds integer handles, Rust owns the pixels.

**pil-rust-python** bridges Rust to RustPython via `#[pymodule]`, converting between Python objects and Rust types.

**PIL/\*.py** provides the user-facing API that matches Pillow's interface, calling into `_pil_native` for operations.

## Supported Modules

| Module | Coverage |
|--------|----------|
| `Image` | new, open, save, convert, resize, crop, rotate, transpose, transform, paste, split, merge, blend, composite, filter, quantize, and more |
| `ImageDraw` | rectangle, ellipse, line, polygon, arc, pieslice, text, rounded_rectangle, regular_polygon, point, chord |
| `ImageFilter` | BLUR, SHARPEN, SMOOTH, GaussianBlur, UnsharpMask, CONTOUR, DETAIL, EMBOSS, FIND_EDGES, EDGE_ENHANCE, Kernel, RankFilter, MedianFilter, MinFilter, MaxFilter |
| `ImageEnhance` | Brightness, Contrast, Color, Sharpness |
| `ImageOps` | grayscale, flip, mirror, invert, autocontrast, equalize, solarize, posterize, pad, contain, cover, expand, crop, colorize, scale |
| `ImageColor` | getrgb, getcolor — named colors, hex, rgb(), rgba(), hsl() |
| `ImageChops` | add, subtract, multiply, screen, overlay, soft_light, hard_light, darker, lighter, difference, invert, offset |
| `ImageStat` | mean, median, stddev, rms, extrema, count, sum, var |
| `ImageFont` | built-in 8x16 bitmap font (truetype/load_default return it) |
| `ImagePath` | Path with tolist, getbbox, compact, map, transform |
| `ImageSequence` | Iterator (single-frame) |

**Supported modes:** L, LA, RGB, RGBA, 1 (binary)

**Supported formats:** PNG, JPEG (with quality=), GIF, BMP, TIFF, WebP

See [docs/PIL-STATUS.md](docs/PIL-STATUS.md) for the full feature matrix.

## Building

pillow-rust is compiled as part of the Codepod WASM Python runtime:

```bash
# From the codepod repo root
PYTHON_FEATURES="numpy,pil" bash scripts/build-mcp.sh --rebuild-python
```

For Rust-only development:

```bash
cd packages/pillow-rust
cargo build
cargo test
```

## Tests

### Unit tests (Rust-hosted)

```bash
cargo test
```

Runs 173+ tests via `tests/python/run_all.py` using RustPython.

### Upstream compatibility tests

`tests/pillow_compat/` contains vendored upstream Pillow tests adapted to run in our environment. These track compatibility with real Pillow using an xfail list for known gaps:

```bash
# Inside a Codepod sandbox after `pip install PIL`:
cd tests/pillow_compat
python3 run_compat.py --verbose

# CI mode (only fails on unexpected failures):
python3 run_compat.py --ci
```

Current status: 42 passed, 8 xfailed across 10 upstream test files.

## Not implemented

- Modes: P (palette), I (32-bit int), F (32-bit float), CMYK
- TrueType font rendering (bitmap font only)
- EXIF metadata
- ImageGrab, ImageTk (N/A in WASM)
- ImageMorph
- Multi-frame GIF/TIFF
