# Pillow Compatibility Tier 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 5 high-impact Pillow-compatible features: thumbnail, save quality params, ImageOps, ImageEnhance, and polygon drawing.

**Architecture:** Features split into Rust core (pixel math, JPEG encoding, polygon scanline fill), Python bindings (thin wrappers exposing to RustPython VM), and pure-Python PIL modules (ImageOps, ImageEnhance, thumbnail). Pure-Python features use existing primitives (resize, paste, point, getextrema) to avoid unnecessary Rust code.

**Tech Stack:** Rust `image` crate (JpegEncoder for quality), RustPython VM bindings, Python PIL layer.

---

### Task 1: Image.thumbnail() — pure Python

**Files:**
- Modify: `python/PIL/Image.py` (Image class, add `thumbnail` method after `resize`)
- Create: `tests/python/test_image_thumbnail_upstream.py`

**Step 1: Write test file**

Create `tests/python/test_image_thumbnail_upstream.py`:

```python
"""Tests for Image.thumbnail() — aspect-ratio-preserving resize."""

from PIL import Image


def test_thumbnail_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    im.thumbnail((100, 100))
    assert im.size == (100, 50)
    assert im.getpixel((0, 0)) == (255, 0, 0)


def test_thumbnail_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    im.thumbnail((100, 100))
    assert im.size == (50, 100)
    assert im.getpixel((0, 0)) == (0, 255, 0)


def test_thumbnail_square():
    im = Image.new("RGB", (200, 200), (0, 0, 255))
    im.thumbnail((100, 100))
    assert im.size == (100, 100)


def test_thumbnail_already_smaller():
    im = Image.new("RGB", (50, 30))
    im.thumbnail((100, 100))
    assert im.size == (50, 30)  # unchanged


def test_thumbnail_exact_fit():
    im = Image.new("RGB", (100, 100))
    im.thumbnail((100, 100))
    assert im.size == (100, 100)


def test_thumbnail_L_mode():
    im = Image.new("L", (200, 100), 128)
    im.thumbnail((50, 50))
    assert im.size == (50, 25)
    assert im.mode == "L"


def test_thumbnail_RGBA_mode():
    im = Image.new("RGBA", (200, 100), (255, 0, 0, 128))
    im.thumbnail((50, 50))
    assert im.size == (50, 25)
    assert im.mode == "RGBA"


def test_thumbnail_modifies_in_place():
    im = Image.new("RGB", (200, 100))
    original_id = id(im)
    im.thumbnail((100, 100))
    assert id(im) == original_id  # same object


def test_thumbnail_non_square_target():
    im = Image.new("RGB", (400, 200))
    im.thumbnail((200, 50))
    # Must fit in 200x50: 400/200=2, 200/50=4, scale by 4
    assert im.size == (100, 50)
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/pil-python -m pytest tests/python/test_image_thumbnail_upstream.py -v`
Expected: FAIL — `AttributeError: 'Image' object has no attribute 'thumbnail'`

**Step 3: Implement thumbnail in Image.py**

Add this method to the `Image` class in `python/PIL/Image.py`, after the `resize` method (around line 193):

```python
    def thumbnail(self, size, resample=None, **_kw):
        """Modify the image in-place to fit within *size*, preserving aspect ratio.

        Only shrinks — never enlarges.
        """
        w, h = self.size
        max_w, max_h = size
        if w <= max_w and h <= max_h:
            return
        # Scale by the larger ratio to fit within bounds
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        new_im = self.resize((new_w, new_h), resample=resample)
        # Replace handle in-place
        _pil_native.image_close(self._handle)
        self._handle = new_im._handle
        new_im._handle = None  # prevent double-close
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/pil-python -m pytest tests/python/test_image_thumbnail_upstream.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add python/PIL/Image.py tests/python/test_image_thumbnail_upstream.py
git commit -m "feat: add Image.thumbnail() with aspect-ratio preservation"
```

---

### Task 2: save() quality/optimize params — Rust core + bindings + Python

**Files:**
- Modify: `crates/pil-rust-core/src/lib.rs` (add `save_with_quality` function after `save`)
- Modify: `crates/pil-rust-python/src/lib.rs` (update `image_save` to accept quality param)
- Modify: `python/PIL/Image.py` (update `save` method to pass quality)
- Create: `tests/python/test_image_save_quality.py`

**Step 1: Write test file**

Create `tests/python/test_image_save_quality.py`:

```python
"""Tests for save() quality and optimize parameters."""

from PIL import Image


def test_save_jpeg_default_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_default.jpg")
    im2 = Image.open("/tmp/_pil_quality_default.jpg")
    assert im2.size == (100, 100)


def test_save_jpeg_low_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_low.jpg", quality=10)
    im2 = Image.open("/tmp/_pil_quality_low.jpg")
    assert im2.size == (100, 100)


def test_save_jpeg_high_quality():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    im.save("/tmp/_pil_quality_high.jpg", quality=95)
    im2 = Image.open("/tmp/_pil_quality_high.jpg")
    assert im2.size == (100, 100)


def test_save_quality_affects_file_size():
    im = Image.new("RGB", (200, 200))
    for y in range(200):
        for x in range(200):
            im.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))
    im.save("/tmp/_pil_q10.jpg", quality=10)
    im.save("/tmp/_pil_q95.jpg", quality=95)
    _open = __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
    with _open("/tmp/_pil_q10.jpg", "rb") as f:
        size_low = len(f.read())
    with _open("/tmp/_pil_q95.jpg", "rb") as f:
        size_high = len(f.read())
    assert size_low < size_high


def test_save_png_ignores_quality():
    """PNG doesn't use quality — should save normally without error."""
    im = Image.new("RGB", (50, 50), (0, 255, 0))
    im.save("/tmp/_pil_quality_png.png", quality=50)
    im2 = Image.open("/tmp/_pil_quality_png.png")
    assert im2.getpixel((0, 0)) == (0, 255, 0)


def test_save_jpeg_roundtrip_color():
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    im.save("/tmp/_pil_quality_rt.jpg", quality=100)
    im2 = Image.open("/tmp/_pil_quality_rt.jpg")
    r, g, b = im2.getpixel((5, 5))
    assert r > 200  # JPEG is lossy, but at q=100 close to original


def test_save_optimize_flag():
    """optimize=True should not error."""
    im = Image.new("RGB", (50, 50), (0, 0, 255))
    im.save("/tmp/_pil_optimize.jpg", optimize=True)
    im2 = Image.open("/tmp/_pil_optimize.jpg")
    assert im2.size == (50, 50)
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/pil-python -m pytest tests/python/test_image_save_quality.py -v`
Expected: FAIL (quality param not wired through)

**Step 3: Add `save_with_quality` to Rust core**

In `crates/pil-rust-core/src/lib.rs`, add after the existing `save` function (line ~95):

```rust
pub fn save_with_quality(handle: &ImageHandle, format: &str, quality: u8) -> Result<Vec<u8>> {
    let fmt = parse_format(format)?;
    let mut buf = Cursor::new(Vec::new());
    match fmt {
        ImageFormat::Jpeg => {
            use image::codecs::jpeg::JpegEncoder;
            use image::ImageEncoder;
            let rgb = handle.inner.to_rgb8();
            let (w, h) = handle.inner.dimensions();
            let encoder = JpegEncoder::new_with_quality(&mut buf, quality);
            encoder
                .write_image(rgb.as_raw(), w, h, image::ExtendedColorType::Rgb8)
                .map_err(PilError::Image)?;
        }
        _ => {
            handle.inner.write_to(&mut buf, fmt)?;
        }
    }
    Ok(buf.into_inner())
}
```

**Step 4: Update Python binding**

In `crates/pil-rust-python/src/lib.rs`, replace the `image_save` function:

```rust
    #[pyfunction]
    fn image_save(
        handle_id: usize,
        format: String,
        quality: vm::function::OptionalArg<u8>,
        vm: &VirtualMachine,
    ) -> PyResult<Vec<u8>> {
        let q = quality.into_option();
        with(handle_id, |h| {
            if let Some(q) = q {
                pil_rust_core::save_with_quality(h, &format, q)
            } else {
                pil_rust_core::save(h, &format)
            }
        })
        .map_err(|e| vm.new_value_error(e))?
        .map_err(|e| vm.new_value_error(e.to_string()))
    }
```

**Step 5: Update Python Image.save()**

In `python/PIL/Image.py`, update the `save` method to pass quality:

```python
    def save(self, fp, format=None, **params):
        """Save the image to *fp* (filename or file-like object)."""
        if format is None and isinstance(fp, str):
            ext = fp.rsplit(".", 1)[-1] if "." in fp else ""
            format = ext.lower() or "png"
        fmt = format or "png"
        quality = params.get("quality")
        if quality is not None:
            data = _pil_native.image_save(self._handle, fmt, int(quality))
        else:
            data = _pil_native.image_save(self._handle, fmt)
        if isinstance(fp, str):
            with __builtins__["open"](fp, "wb") if isinstance(__builtins__, dict) else __builtins__.open(fp, "wb") as f:
                f.write(data)
        else:
            fp.write(data)
```

**Step 6: Build and run tests**

Run: `cargo build -p pil-rust-wasm && target/debug/pil-python -m pytest tests/python/test_image_save_quality.py -v`
Expected: all PASS

**Step 7: Commit**

```bash
git add crates/pil-rust-core/src/lib.rs crates/pil-rust-python/src/lib.rs python/PIL/Image.py tests/python/test_image_save_quality.py
git commit -m "feat: add JPEG quality parameter to save()"
```

---

### Task 3: ImageOps module — pure Python

**Files:**
- Create: `python/PIL/ImageOps.py`
- Create: `tests/python/test_imageops_upstream.py`

**Step 1: Write test file**

Create `tests/python/test_imageops_upstream.py`:

```python
"""Tests for PIL.ImageOps module."""

from PIL import Image, ImageOps


# --- autocontrast ---

def test_autocontrast_L():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 200)
    out = ImageOps.autocontrast(im)
    assert out.mode == "L"
    assert out.size == (10, 10)
    mn, mx = out.getextrema()
    assert mn == 0
    assert mx == 255


def test_autocontrast_RGB():
    im = Image.new("RGB", (10, 10), (100, 100, 100))
    im.putpixel((0, 0), (50, 60, 70))
    im.putpixel((1, 0), (200, 210, 220))
    out = ImageOps.autocontrast(im)
    assert out.mode == "RGB"


def test_autocontrast_flat():
    """All same value — should not crash, all pixels become 0."""
    im = Image.new("L", (10, 10), 128)
    out = ImageOps.autocontrast(im)
    assert out.getpixel((0, 0)) == 0


# --- contain ---

def test_contain_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (100, 50)


def test_contain_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 100)


def test_contain_already_fits():
    im = Image.new("RGB", (50, 30))
    out = ImageOps.contain(im, (100, 100))
    assert out.size == (50, 30)


# --- fit ---

def test_fit_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_portrait():
    im = Image.new("RGB", (100, 300), (0, 255, 0))
    out = ImageOps.fit(im, (100, 100))
    assert out.size == (100, 100)


def test_fit_square():
    im = Image.new("RGB", (200, 200))
    out = ImageOps.fit(im, (50, 50))
    assert out.size == (50, 50)


# --- pad ---

def test_pad_landscape():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)
    # Padding should be black by default
    assert out.getpixel((0, 0)) == (0, 0, 0)
    # Center should have image content
    assert out.getpixel((100, 100)) == (255, 0, 0)


def test_pad_portrait():
    im = Image.new("RGB", (100, 200), (0, 255, 0))
    out = ImageOps.pad(im, (200, 200))
    assert out.size == (200, 200)


def test_pad_with_color():
    im = Image.new("RGB", (200, 100), (255, 0, 0))
    out = ImageOps.pad(im, (200, 200), color=(0, 0, 255))
    assert out.size == (200, 200)
    # Corner should be fill color
    assert out.getpixel((0, 0)) == (0, 0, 255)


def test_pad_already_fits():
    im = Image.new("RGB", (100, 100), (255, 0, 0))
    out = ImageOps.pad(im, (100, 100))
    assert out.size == (100, 100)
    assert out.getpixel((0, 0)) == (255, 0, 0)


# --- expand ---

def test_expand_default_black():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=10)
    assert out.size == (70, 70)
    assert out.getpixel((0, 0)) == (0, 0, 0)
    assert out.getpixel((10, 10)) == (255, 0, 0)


def test_expand_with_fill():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=5, fill=(0, 0, 255))
    assert out.size == (60, 60)
    assert out.getpixel((0, 0)) == (0, 0, 255)
    assert out.getpixel((5, 5)) == (255, 0, 0)


def test_expand_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(10, 20))
    assert out.size == (70, 90)


def test_expand_four_tuple_border():
    im = Image.new("RGB", (50, 50), (255, 0, 0))
    out = ImageOps.expand(im, border=(5, 10, 15, 20))
    assert out.size == (70, 80)
    assert out.getpixel((5, 10)) == (255, 0, 0)


def test_expand_L_mode():
    im = Image.new("L", (50, 50), 128)
    out = ImageOps.expand(im, border=5, fill=0)
    assert out.size == (60, 60)
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((5, 5)) == 128
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/pil-python -m pytest tests/python/test_imageops_upstream.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'PIL.ImageOps'`

**Step 3: Create ImageOps.py**

Create `python/PIL/ImageOps.py`:

```python
"""
PIL.ImageOps — ready-made image processing operations.
"""

from PIL import Image


def autocontrast(image, cutoff=0, ignore=None):
    """Maximize image contrast by remapping pixel values to span 0–255."""
    bands = image.getbands()
    if len(bands) == 1:
        # Single channel
        extrema = image.getextrema()
        lo, hi = extrema
        if lo >= hi:
            return image.point(lambda x: 0)
        scale = 255.0 / (hi - lo)
        offset = lo
        lut = [max(0, min(255, int((i - offset) * scale))) for i in range(256)]
        return image.point(lut)
    else:
        # Multi-channel: split, autocontrast each, merge
        channels = image.split()
        result_channels = []
        for ch in channels:
            result_channels.append(autocontrast(ch))
        return Image.merge(image.mode, result_channels)


def contain(image, size, method=None):
    """Resize to fit within *size*, preserving aspect ratio. Returns new image."""
    w, h = image.size
    max_w, max_h = size
    if w <= max_w and h <= max_h:
        return image.copy()
    scale = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), resample=method)


def fit(image, size, method=None, centering=(0.5, 0.5)):
    """Resize and crop to fill *size* exactly, preserving aspect ratio."""
    target_w, target_h = size
    src_w, src_h = image.size
    # Scale so the smaller dimension matches the target
    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), resample=method)
    # Crop from center
    cx, cy = centering
    left = int((new_w - target_w) * cx)
    top = int((new_h - target_h) * cy)
    return resized.crop((left, top, left + target_w, top + target_h))


def pad(image, size, method=None, color=None, centering=(0.5, 0.5)):
    """Resize to fit within *size* and pad to fill exactly."""
    target_w, target_h = size
    # Contain first
    contained = contain(image, size, method=method)
    cw, ch = contained.size
    if cw == target_w and ch == target_h:
        return contained
    # Create canvas with fill color
    fill = color if color is not None else 0
    out = Image.new(image.mode, (target_w, target_h), fill)
    # Paste centered
    cx, cy = centering
    left = int((target_w - cw) * cx)
    top = int((target_h - ch) * cy)
    out.paste(contained, (left, top))
    return out


def expand(image, border=0, fill=0):
    """Add a border around the image.

    *border* can be an int, 2-tuple (left/right, top/bottom),
    or 4-tuple (left, top, right, bottom).
    """
    if isinstance(border, int):
        left = top = right = bottom = border
    elif len(border) == 2:
        left = right = border[0]
        top = bottom = border[1]
    elif len(border) == 4:
        left, top, right, bottom = border
    else:
        raise ValueError("border must be int, 2-tuple, or 4-tuple")
    w, h = image.size
    out = Image.new(image.mode, (w + left + right, h + top + bottom), fill)
    out.paste(image, (left, top))
    return out
```

**Step 4: Run tests to verify they pass**

Run: `target/debug/pil-python -m pytest tests/python/test_imageops_upstream.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add python/PIL/ImageOps.py tests/python/test_imageops_upstream.py
git commit -m "feat: add ImageOps module (autocontrast, contain, fit, pad, expand)"
```

---

### Task 4: ImageEnhance module — Rust core + bindings + Python

**Files:**
- Modify: `crates/pil-rust-core/src/lib.rs` (add enhance functions)
- Modify: `crates/pil-rust-python/src/lib.rs` (add `image_enhance` binding)
- Create: `python/PIL/ImageEnhance.py`
- Create: `tests/python/test_imageenhance_upstream.py`

**Step 1: Write test file**

Create `tests/python/test_imageenhance_upstream.py`:

```python
"""Tests for PIL.ImageEnhance module."""

from PIL import Image, ImageEnhance


# --- Brightness ---

def test_brightness_factor_0():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Brightness(im).enhance(0.0)
    assert out.getpixel((5, 5)) == (0, 0, 0)


def test_brightness_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Brightness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_brightness_factor_2():
    im = Image.new("RGB", (10, 10), (100, 50, 25))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    px = out.getpixel((5, 5))
    assert px == (200, 100, 50)


def test_brightness_clamp():
    im = Image.new("RGB", (10, 10), (200, 200, 200))
    out = ImageEnhance.Brightness(im).enhance(2.0)
    px = out.getpixel((5, 5))
    assert px == (255, 255, 255)


def test_brightness_L():
    im = Image.new("L", (10, 10), 100)
    out = ImageEnhance.Brightness(im).enhance(0.5)
    assert out.getpixel((5, 5)) == 50


# --- Contrast ---

def test_contrast_factor_0():
    """Factor 0 should produce a uniform gray image."""
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Contrast(im).enhance(0.0)
    px = out.getpixel((5, 5))
    # All channels should be the same gray value
    assert px[0] == px[1] == px[2]


def test_contrast_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_contrast_L():
    im = Image.new("L", (10, 10), 100)
    out = ImageEnhance.Contrast(im).enhance(1.0)
    assert out.getpixel((5, 5)) == 100


# --- Color (saturation) ---

def test_color_factor_0():
    """Factor 0 should produce grayscale."""
    im = Image.new("RGB", (10, 10), (255, 0, 0))
    out = ImageEnhance.Color(im).enhance(0.0)
    px = out.getpixel((5, 5))
    assert px[0] == px[1] == px[2]  # grayscale


def test_color_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Color(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


# --- Sharpness ---

def test_sharpness_factor_0():
    """Factor 0 should be blurred."""
    im = Image.new("RGB", (20, 20), (0, 0, 0))
    im.putpixel((10, 10), (255, 255, 255))
    out = ImageEnhance.Sharpness(im).enhance(0.0)
    assert out.size == (20, 20)
    assert out.mode == "RGB"


def test_sharpness_factor_1():
    im = Image.new("RGB", (10, 10), (200, 100, 50))
    out = ImageEnhance.Sharpness(im).enhance(1.0)
    assert out.getpixel((5, 5)) == (200, 100, 50)


def test_sharpness_factor_2():
    im = Image.new("RGB", (20, 20), (100, 100, 100))
    out = ImageEnhance.Sharpness(im).enhance(2.0)
    assert out.size == (20, 20)


# --- General ---

def test_enhance_preserves_size():
    im = Image.new("RGB", (50, 30), (100, 150, 200))
    for Enhancer in [ImageEnhance.Brightness, ImageEnhance.Contrast,
                     ImageEnhance.Color, ImageEnhance.Sharpness]:
        out = Enhancer(im).enhance(1.5)
        assert out.size == (50, 30)
        assert out.mode == "RGB"
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/pil-python -m pytest tests/python/test_imageenhance_upstream.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Add enhance function to Rust core**

In `crates/pil-rust-core/src/lib.rs`, add after the `point` function (near end of file, before helpers):

```rust
// ---------------------------------------------------------------------------
// enhance — pixel-level brightness/contrast/color/sharpness
// ---------------------------------------------------------------------------

/// Enhance image: `kind` is one of "brightness", "contrast", "color", "sharpness".
/// `factor`: 0.0 = degenerate, 1.0 = original, >1.0 = enhanced.
pub fn enhance(handle: &ImageHandle, kind: &str, factor: f32) -> Result<ImageHandle> {
    match kind {
        "brightness" => Ok(enhance_brightness(handle, factor)),
        "contrast" => Ok(enhance_contrast(handle, factor)),
        "color" => Ok(enhance_color(handle, factor)),
        "sharpness" => enhance_sharpness(handle, factor),
        _ => Err(PilError::InvalidOperation(format!(
            "unknown enhance kind: {kind}"
        ))),
    }
}

fn enhance_brightness(handle: &ImageHandle, factor: f32) -> ImageHandle {
    // Degenerate = black image. Blend: pixel * factor
    let rgba = handle.inner.to_rgba8();
    let (w, h) = handle.inner.dimensions();
    let mut out = ImageBuffer::new(w, h);
    for (x, y, px) in rgba.enumerate_pixels() {
        let r = (px[0] as f32 * factor).round().clamp(0.0, 255.0) as u8;
        let g = (px[1] as f32 * factor).round().clamp(0.0, 255.0) as u8;
        let b = (px[2] as f32 * factor).round().clamp(0.0, 255.0) as u8;
        out.put_pixel(x, y, image::Rgba([r, g, b, px[3]]));
    }
    let dyn_img = DynamicImage::ImageRgba8(out);
    let converted = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(dyn_img.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(dyn_img.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(dyn_img.to_rgb8()),
        _ => dyn_img,
    };
    ImageHandle { inner: converted }
}

fn enhance_contrast(handle: &ImageHandle, factor: f32) -> ImageHandle {
    // Degenerate = mean-gray image. Blend between mean-gray and original.
    let rgba = handle.inner.to_rgba8();
    let (w, h) = handle.inner.dimensions();
    // Compute mean luminance
    let mut sum: f64 = 0.0;
    let mut count: u64 = 0;
    for px in rgba.pixels() {
        let lum = 0.299 * px[0] as f64 + 0.587 * px[1] as f64 + 0.114 * px[2] as f64;
        sum += lum;
        count += 1;
    }
    let mean = if count > 0 { (sum / count as f64).round() as u8 } else { 128 };

    let mut out = ImageBuffer::new(w, h);
    for (x, y, px) in rgba.enumerate_pixels() {
        let r = (mean as f32 + (px[0] as f32 - mean as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        let g = (mean as f32 + (px[1] as f32 - mean as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        let b = (mean as f32 + (px[2] as f32 - mean as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        out.put_pixel(x, y, image::Rgba([r, g, b, px[3]]));
    }
    let dyn_img = DynamicImage::ImageRgba8(out);
    let converted = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(dyn_img.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(dyn_img.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(dyn_img.to_rgb8()),
        _ => dyn_img,
    };
    ImageHandle { inner: converted }
}

fn enhance_color(handle: &ImageHandle, factor: f32) -> ImageHandle {
    // Degenerate = grayscale version. Blend between grayscale and original.
    let rgba = handle.inner.to_rgba8();
    let (w, h) = handle.inner.dimensions();
    let mut out = ImageBuffer::new(w, h);
    for (x, y, px) in rgba.enumerate_pixels() {
        let lum = (0.299 * px[0] as f32 + 0.587 * px[1] as f32 + 0.114 * px[2] as f32)
            .round()
            .clamp(0.0, 255.0) as u8;
        let r = (lum as f32 + (px[0] as f32 - lum as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        let g = (lum as f32 + (px[1] as f32 - lum as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        let b = (lum as f32 + (px[2] as f32 - lum as f32) * factor)
            .round()
            .clamp(0.0, 255.0) as u8;
        out.put_pixel(x, y, image::Rgba([r, g, b, px[3]]));
    }
    let dyn_img = DynamicImage::ImageRgba8(out);
    let converted = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(dyn_img.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(dyn_img.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(dyn_img.to_rgb8()),
        _ => dyn_img,
    };
    ImageHandle { inner: converted }
}

fn enhance_sharpness(handle: &ImageHandle, factor: f32) -> Result<ImageHandle> {
    // Degenerate = blurred image. Blend between blurred and original.
    // At factor=2.0, we sharpen (original + (original - blurred)).
    let rgba = handle.inner.to_rgba8();
    let (w, h) = handle.inner.dimensions();
    let blurred = handle.inner.blur(1.0).to_rgba8();

    let mut out = ImageBuffer::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let orig = rgba.get_pixel(x, y);
            let blur = blurred.get_pixel(x, y);
            let r = (blur[0] as f32 + (orig[0] as f32 - blur[0] as f32) * factor)
                .round()
                .clamp(0.0, 255.0) as u8;
            let g = (blur[1] as f32 + (orig[1] as f32 - blur[1] as f32) * factor)
                .round()
                .clamp(0.0, 255.0) as u8;
            let b = (blur[2] as f32 + (orig[2] as f32 - blur[2] as f32) * factor)
                .round()
                .clamp(0.0, 255.0) as u8;
            out.put_pixel(x, y, image::Rgba([r, g, b, orig[3]]));
        }
    }
    let dyn_img = DynamicImage::ImageRgba8(out);
    let converted = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(dyn_img.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(dyn_img.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(dyn_img.to_rgb8()),
        _ => dyn_img,
    };
    Ok(ImageHandle { inner: converted })
}
```

**Step 4: Add Python binding**

In `crates/pil-rust-python/src/lib.rs`, add before the Helpers section:

```rust
    // -- enhance ---------------------------------------------------------------

    #[pyfunction]
    fn image_enhance(
        handle_id: usize,
        kind: String,
        factor: f32,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        let handle_clone = with(handle_id, |h| h.clone()).map_err(|e| vm.new_value_error(e))?;
        pil_rust_core::enhance(&handle_clone, &kind, factor)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }
```

**Step 5: Create ImageEnhance.py**

Create `python/PIL/ImageEnhance.py`:

```python
"""
PIL.ImageEnhance — image enhancement classes.
"""

import _pil_native
from PIL.Image import Image


class _Enhancer:
    """Base class for image enhancers."""

    def __init__(self, image):
        self._image = image
        self._kind = ""

    def enhance(self, factor):
        """Return an enhanced copy. factor=1.0 returns original."""
        new_handle = _pil_native.image_enhance(
            self._image._handle, self._kind, float(factor)
        )
        return Image(new_handle)


class Brightness(_Enhancer):
    """Adjust image brightness. factor=0.0 is black, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "brightness"


class Contrast(_Enhancer):
    """Adjust image contrast. factor=0.0 is solid gray, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "contrast"


class Color(_Enhancer):
    """Adjust color saturation. factor=0.0 is grayscale, 1.0 is original."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "color"


class Sharpness(_Enhancer):
    """Adjust image sharpness. factor=0.0 is blurred, 1.0 is original, 2.0 is sharpened."""

    def __init__(self, image):
        super().__init__(image)
        self._kind = "sharpness"
```

**Step 6: Build and run tests**

Run: `cargo build -p pil-rust-wasm && target/debug/pil-python -m pytest tests/python/test_imageenhance_upstream.py -v`
Expected: all PASS

**Step 7: Commit**

```bash
git add crates/pil-rust-core/src/lib.rs crates/pil-rust-python/src/lib.rs python/PIL/ImageEnhance.py tests/python/test_imageenhance_upstream.py
git commit -m "feat: add ImageEnhance module (Brightness, Contrast, Color, Sharpness)"
```

---

### Task 5: ImageDraw.polygon() — Rust core + binding + Python

**Files:**
- Modify: `crates/pil-rust-core/src/lib.rs` (add `draw_polygon` function)
- Modify: `crates/pil-rust-python/src/lib.rs` (add `draw_polygon` binding)
- Modify: `python/PIL/ImageDraw.py` (add `polygon` method)
- Create: `tests/python/test_imagedraw_polygon.py`

**Step 1: Write test file**

Create `tests/python/test_imagedraw_polygon.py`:

```python
"""Tests for ImageDraw.polygon()."""

from PIL import Image, ImageDraw


def test_polygon_triangle_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(50, 10), (10, 90), (90, 90)], fill=(255, 0, 0))
    # Center of triangle should be filled
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Outside should be black
    assert im.getpixel((5, 5)) == (0, 0, 0)


def test_polygon_rectangle_fill():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], fill=(0, 255, 0))
    assert im.getpixel((50, 50)) == (0, 255, 0)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_polygon_outline_only():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], outline=(0, 0, 255))
    # Edge should be drawn
    assert im.getpixel((20, 20)) == (0, 0, 255)
    assert im.getpixel((50, 20)) == (0, 0, 255)
    # Interior should be empty
    assert im.getpixel((50, 50)) == (0, 0, 0)


def test_polygon_flat_coords():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([20, 20, 80, 20, 80, 80, 20, 80], fill=(128, 128, 128))
    assert im.getpixel((50, 50)) == (128, 128, 128)


def test_polygon_fill_and_outline():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)],
                 fill=(255, 0, 0), outline=(0, 255, 0))
    # Interior should be fill color
    assert im.getpixel((50, 50)) == (255, 0, 0)
    # Edge should be outline color
    assert im.getpixel((20, 20)) == (0, 255, 0)


def test_polygon_pentagon():
    im = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(50, 10), (90, 40), (75, 85), (25, 85), (10, 40)],
                 fill=(0, 0, 255))
    assert im.getpixel((50, 50)) == (0, 0, 255)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_polygon_L_mode():
    im = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(im)
    draw.polygon([(20, 20), (80, 20), (80, 80), (20, 80)], fill=200)
    assert im.getpixel((50, 50)) == 200
```

**Step 2: Run tests to verify they fail**

Run: `target/debug/pil-python -m pytest tests/python/test_imagedraw_polygon.py -v`
Expected: FAIL — `AttributeError: 'ImageDraw' object has no attribute 'polygon'`

**Step 3: Add `draw_polygon` to Rust core**

In `crates/pil-rust-core/src/lib.rs`, add after `draw_ellipse` (before the font data):

```rust
/// Draw a filled or outlined polygon.
///
/// `points` is a flat list of (x, y) pairs: [x0, y0, x1, y1, ...].
/// Uses scanline fill for filled polygons, Bresenham lines for outline.
pub fn draw_polygon(handle: &mut ImageHandle, points: &[i32], color: [u8; 4], fill: bool) {
    let n = points.len() / 2;
    if n < 3 {
        return;
    }

    let (w, h) = handle.inner.dimensions();
    let pixel = image::Rgba(color);

    if fill {
        // Find bounding box
        let mut min_y = i32::MAX;
        let mut max_y = i32::MIN;
        for i in 0..n {
            let y = points[i * 2 + 1];
            if y < min_y {
                min_y = y;
            }
            if y > max_y {
                max_y = y;
            }
        }
        min_y = min_y.max(0);
        max_y = max_y.min(h as i32 - 1);

        // Scanline fill
        for y in min_y..=max_y {
            let mut intersections = Vec::new();
            for i in 0..n {
                let j = (i + 1) % n;
                let y0 = points[i * 2 + 1];
                let y1 = points[j * 2 + 1];
                if (y0 <= y && y1 > y) || (y1 <= y && y0 > y) {
                    let x0 = points[i * 2] as f64;
                    let x1 = points[j * 2] as f64;
                    let t = (y as f64 - y0 as f64) / (y1 as f64 - y0 as f64);
                    let x = (x0 + t * (x1 - x0)).round() as i32;
                    intersections.push(x);
                }
            }
            intersections.sort();
            // Fill between pairs of intersections
            let mut i = 0;
            while i + 1 < intersections.len() {
                let x_start = intersections[i].max(0);
                let x_end = intersections[i + 1].min(w as i32 - 1);
                for x in x_start..=x_end {
                    handle.inner.put_pixel(x as u32, y as u32, pixel);
                }
                i += 2;
            }
        }
    }

    // Draw outline (always for outline-only, or after fill when outline requested)
    if !fill {
        for i in 0..n {
            let j = (i + 1) % n;
            let x0 = points[i * 2];
            let y0 = points[i * 2 + 1];
            let x1 = points[j * 2];
            let y1 = points[j * 2 + 1];
            draw_line(handle, x0, y0, x1, y1, color, 1);
        }
    }
}
```

**Step 4: Add Python binding**

In `crates/pil-rust-python/src/lib.rs`, add after `draw_text`:

```rust
    #[pyfunction]
    fn draw_polygon(
        handle_id: usize,
        xy: Vec<i32>,
        color: PyObjectRef,
        fill: bool,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_polygon(h, &xy, c, fill)
        })
        .map_err(|e| vm.new_value_error(e))
    }
```

**Step 5: Add polygon method to ImageDraw.py**

In `python/PIL/ImageDraw.py`, add after the `line` method:

```python
    def polygon(self, xy, fill=None, outline=None, width=1):
        """Draw a polygon.

        *xy* is either ``[(x0, y0), (x1, y1), ...]`` or ``[x0, y0, x1, y1, ...]``.
        """
        coords = _normalise_xy(xy)
        if fill is not None:
            color = fill
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_polygon(
                self._image._handle, list(coords), list(color), True
            )
        if outline is not None:
            color = outline
            if isinstance(color, int):
                color = (color, color, color)
            _pil_native.draw_polygon(
                self._image._handle, list(coords), list(color), False
            )
        if fill is None and outline is None:
            _pil_native.draw_polygon(
                self._image._handle, list(coords), [255, 255, 255], False
            )
```

**Step 6: Build and run tests**

Run: `cargo build -p pil-rust-wasm && target/debug/pil-python -m pytest tests/python/test_imagedraw_polygon.py -v`
Expected: all PASS

**Step 7: Commit**

```bash
git add crates/pil-rust-core/src/lib.rs crates/pil-rust-python/src/lib.rs python/PIL/ImageDraw.py tests/python/test_imagedraw_polygon.py
git commit -m "feat: add ImageDraw.polygon() with scanline fill"
```

---

### Task 6: Final verification

**Step 1: Run full test suite**

Run: `cargo build -p pil-rust-wasm && target/debug/pil-python -m pytest tests/python/ -v`
Expected: all tests PASS (324 existing + ~60 new ≈ 384 total)

**Step 2: Run lints**

Run: `cargo fmt --all --check && cargo clippy -- -D warnings`
Expected: clean

**Step 3: Fix any issues**

If any tests fail or lint issues, fix them before proceeding.

**Step 4: Final commit if needed**

If any fixes were needed, commit them.
