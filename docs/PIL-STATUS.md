# PIL (Pillow) Implementation Status

Codepod's PIL implementation: a Rust-backed subset of Pillow running in WASM via RustPython.

**Architecture:** Python wrappers (`PIL/`) → RustPython bindings (`pil-rust-python`) → Rust core (`pil-rust-core`)

**Supported modes:** L, LA, RGB, RGBA

**Tests:** 173 passing across 8 test files

---

## Implemented

### PIL.Image

| Feature | Status | Notes |
|---------|--------|-------|
| `Image.new(mode, size, color)` | Done | L, LA, RGB, RGBA |
| `Image.open(fp)` | Done | filename or file-like |
| `Image.frombytes(mode, size, data)` | Done | |
| `Image.fromarray(obj, mode)` | Done | numpy-like arrays |
| `Image.merge(mode, bands)` | Done | |
| `image.save(fp, format)` | Done | PNG, JPEG, GIF, BMP, TIFF, WebP |
| `image.copy()` | Done | |
| `image.close()` | Done | context manager supported |
| `image.convert(mode)` | Done | between L/LA/RGB/RGBA |
| `image.resize(size, resample)` | Done | nearest/bilinear/bicubic/lanczos |
| `image.crop(box)` | Done | |
| `image.rotate(angle, expand)` | Done | counter-clockwise, nearest for arbitrary angles |
| `image.transpose(method)` | Done | all 7 methods |
| `image.thumbnail(size)` | Done | in-place, never upsizes |
| `image.filter(f)` | Done | see ImageFilter |
| `image.paste(im, box, mask)` | Done | alpha blending with mask |
| `image.split()` | Done | returns L-mode channels |
| `image.tobytes()` | Done | |
| `image.getpixel(xy)` | Done | |
| `image.putpixel(xy, color)` | Done | |
| `image.histogram()` | Done | 256 values per channel |
| `image.getbbox()` | Done | |
| `image.getextrema()` | Done | |
| `image.size` / `width` / `height` | Done | |
| `image.mode` | Done | |
| `image.getdata()` | Done | flat list of pixel values |
| `image.putdata(data)` | Done | set all pixels at once |
| `image.point(lut)` | Done | lookup table / callable |
| `image.alpha_composite(im)` | Done | proper alpha compositing |
| `Image.blend(im1, im2, alpha)` | Done | linear interpolation |
| `Image.composite(im1, im2, mask)` | Done | mask-based selection |

### PIL.ImageDraw

| Feature | Status | Notes |
|---------|--------|-------|
| `draw.rectangle(xy, fill, outline, width)` | Done | |
| `draw.ellipse(xy, fill, outline, width)` | Done | |
| `draw.line(xy, fill, width)` | Done | Bresenham with width |
| `draw.polygon(xy, fill, outline)` | Done | scanline fill |
| `draw.arc(xy, start, end, fill)` | Done | |
| `draw.pieslice(xy, start, end, fill, outline)` | Done | |
| `draw.text(xy, text, fill, font, anchor)` | Done | built-in 8x16 bitmap font only |
| `draw.textbbox(xy, text, font)` | Done | bitmap font metrics |
| `draw.textlength(text, font)` | Done | |
| `draw.multiline_text(xy, text, fill, font, spacing)` | Done | splits on newlines |
| `draw.rounded_rectangle(xy, radius, fill, outline)` | Done | falls back to rectangle |
| `draw.regular_polygon(bounding_circle, n_sides, fill)` | Done | |

### PIL.ImageFilter

| Feature | Status | Notes |
|---------|--------|-------|
| `BLUR` | Done | |
| `SHARPEN` | Done | |
| `SMOOTH` | Done | |
| `GaussianBlur(radius)` | Done | configurable radius |
| `SMOOTH_MORE` | Done | |
| `CONTOUR` | Done | edge contour |
| `DETAIL` | Done | detail enhancement |
| `EDGE_ENHANCE` | Done | |
| `EDGE_ENHANCE_MORE` | Done | |
| `EMBOSS` | Done | with offset=128 |
| `FIND_EDGES` | Done | |
| `UnsharpMask(radius, percent, threshold)` | Done | |
| `Kernel((3,3), kernel, scale, offset)` | Done | custom 3x3 convolution |
| `RankFilter(size, rank)` | Done | |
| `MedianFilter(size)` | Done | |
| `MinFilter(size)` | Done | |
| `MaxFilter(size)` | Done | |

### PIL.ImageEnhance

| Feature | Status | Notes |
|---------|--------|-------|
| `Brightness(image).enhance(factor)` | Done | |
| `Contrast(image).enhance(factor)` | Done | |
| `Color(image).enhance(factor)` | Done | saturation |
| `Sharpness(image).enhance(factor)` | Done | |

### PIL.ImageOps

| Feature | Status | Notes |
|---------|--------|-------|
| `grayscale(image)` | Done | |
| `flip(image)` | Done | top-to-bottom |
| `mirror(image)` | Done | left-to-right |
| `invert(image)` | Done | |
| `autocontrast(image)` | Done | histogram stretch |
| `pad(image, size, color, centering)` | Done | |
| `contain(image, size)` | Done | |
| `cover(image, size)` | Done | |
| `fit(image, size)` | Done | alias for cover |
| `scale(image, factor)` | Done | |
| `equalize(image)` | Done | histogram equalization |
| `solarize(image, threshold)` | Done | invert above threshold |
| `posterize(image, bits)` | Done | reduce bits per channel |
| `expand(image, border, fill)` | Done | add border frame |
| `crop(image, border)` | Done | remove border frame |
| `colorize(image, black, white)` | Done | colorize grayscale, supports mid color |
| `exif_transpose(image)` | Done | no-op (no EXIF support) |

### PIL.ImageStat

| Feature | Status | Notes |
|---------|--------|-------|
| `Stat(image, mask)` | Done | pure Python, built on histogram() |
| `.mean` | Done | per-band means |
| `.median` | Done | per-band medians |
| `.stddev` | Done | per-band standard deviations |
| `.rms` | Done | root mean square per band |
| `.extrema` | Done | min/max per band |
| `.count` | Done | pixel count per band |
| `.sum` / `.sum2` | Done | sum and sum-of-squares |
| `.var` | Done | variance per band |

### PIL.ImageColor

| Feature | Status | Notes |
|---------|--------|-------|
| `getrgb(color)` | Done | named, hex (#RGB/#RRGGBB/#RRGGBBAA), rgb(), rgba(), hsl() |
| `getcolor(color, mode)` | Done | converts to L/RGB/RGBA |
| `colormap` | Done | 148 CSS named colors |

### PIL.ImageFont

| Feature | Status | Notes |
|---------|--------|-------|
| `truetype(font, size)` | Done | returns built-in bitmap font at requested size |
| `load_default(size)` | Done | built-in bitmap font |
| `load(filename)` | Done | returns default font |
| `font.getbbox(text)` | Done | |
| `font.getlength(text)` | Done | |
| `font.getsize(text)` | Done | deprecated compat |
| `font.getmetrics()` | Done | |

---

## Missing — High Priority

Features LLMs commonly generate code with.

### ~~PIL.ImageFont~~ — moved to Implemented

### ~~Additional ImageFilter types~~ — moved to Implemented

### ~~Image composition~~ — moved to Implemented

### ~~Pixel bulk operations~~ — moved to Implemented

### ~~ImageDraw additions~~ — moved to Implemented

### ~~ImageDraw additions~~ — moved to Implemented

---

## Missing — Medium Priority

Less common but occasionally used.

### Image transforms

| Feature | Status | Notes |
|---------|--------|-------|
| `image.transform(size, method, data)` | TODO | affine/perspective |
| `image.quantize(colors)` | TODO | color reduction, needs P mode |

### Additional modes

| Feature | Status | Notes |
|---------|--------|-------|
| `P` (palette) | TODO | indexed color |
| `1` (1-bit) | TODO | binary |
| `I` (32-bit signed int) | TODO | |
| `F` (32-bit float) | TODO | |
| `CMYK` | TODO | |

### Image metadata

| Feature | Status | Notes |
|---------|--------|-------|
| `image.info` | TODO | metadata dict |
| `image.format` | TODO | source format string |
| `image.getexif()` | TODO | EXIF data |

### Save options

| Feature | Status | Notes |
|---------|--------|-------|
| JPEG `quality=` | TODO | |
| PNG `optimize=` | TODO | |
| Format-specific params | TODO | |

### ~~ImageOps additions~~ — moved to Implemented

---

## Missing — Low Priority

Rarely used by LLMs.

- `ImageChops` — channel arithmetic (add, subtract, multiply, screen, etc.)
- `ImageMorph` — morphological operations
- `ImagePath` — 2D path objects
- `ImageSequence` — GIF/APNG animation frame iteration
- `ImageGrab` — screen capture (N/A in WASM)
- `ImageTk` — Tkinter integration (N/A in WASM)
- Color space conversions (HSV, LAB, CMYK)
- `image.effect_spread()`, `image.entropy()`
- ICO, TIFF multi-page support

---

## Architecture Notes

- **Handle system:** Thread-local `HashMap<usize, ImageHandle>` with atomic counter. Never call `alloc()` while IMAGES RefCell is borrowed.
- **L-mode caveat:** Functions doing RGBA manipulation then converting back via `to_luma8()` must set R=G=B for correct weighted conversion.
- **Rotation:** PIL rotates CCW; `image` crate rotates CW — 90 and 270 are swapped.
- **TRANSPOSE:** `rotate90().fliph()` — **not** rotate270.
- **TRANSVERSE:** `rotate90().flipv()`.
- **Build:** `PYTHON_FEATURES="numpy,pil" bash scripts/build-mcp.sh --rebuild-python`
- **Tests:** `cargo test` in pillow-rust root runs all 173 tests via `run_all.py`
