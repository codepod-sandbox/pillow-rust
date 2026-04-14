use ab_glyph::{Font, FontArc, PxScale, ScaleFont};
use image::{DynamicImage, GenericImage, GenericImageView, ImageBuffer, ImageFormat, Luma};
use std::io::Cursor;

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

#[derive(Debug)]
pub enum PilError {
    Image(image::ImageError),
    UnsupportedMode(String),
    UnsupportedFormat(String),
    InvalidOperation(String),
}

impl std::fmt::Display for PilError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PilError::Image(e) => write!(f, "{e}"),
            PilError::UnsupportedMode(m) => write!(f, "unrecognized image mode: {m}"),
            PilError::UnsupportedFormat(s) => write!(f, "unsupported format: {s}"),
            PilError::InvalidOperation(s) => write!(f, "{s}"),
        }
    }
}

impl std::error::Error for PilError {}

impl From<image::ImageError> for PilError {
    fn from(e: image::ImageError) -> Self {
        PilError::Image(e)
    }
}

pub type Result<T> = std::result::Result<T, PilError>;

// ---------------------------------------------------------------------------
// ImageHandle — thin wrapper around DynamicImage
// ---------------------------------------------------------------------------

pub struct ImageHandle {
    pub inner: DynamicImage,
    pub mode_override: Option<&'static str>,
    /// Flat palette bytes: 256 entries × 3 (RGB) or 4 (RGBA) bytes.
    pub palette: Option<Vec<u8>>,
    /// Mode of the stored palette bytes: "RGB" or "RGBA".
    pub palette_mode: Option<String>,
}

impl ImageHandle {
    /// Construct with no palette (the common case).
    pub fn new(inner: DynamicImage) -> Self {
        Self {
            inner,
            mode_override: None,
            palette: None,
            palette_mode: None,
        }
    }
    /// Construct with a mode override and no palette.
    pub fn with_mode(inner: DynamicImage, mode: &'static str) -> Self {
        Self {
            inner,
            mode_override: Some(mode),
            palette: None,
            palette_mode: None,
        }
    }
}

impl Clone for ImageHandle {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
            mode_override: self.mode_override,
            palette: self.palette.clone(),
            palette_mode: self.palette_mode.clone(),
        }
    }
}

// ---------------------------------------------------------------------------
// Decode / encode
// ---------------------------------------------------------------------------

pub fn open(bytes: &[u8]) -> Result<ImageHandle> {
    let img = image::load_from_memory(bytes)?;
    Ok(ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

pub fn new_image(mode: &str, width: u32, height: u32, color: &[u8]) -> Result<ImageHandle> {
    let img = match mode {
        "RGB" => {
            let (r, g, b) = parse_rgb(color);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgb([r, g, b]));
            DynamicImage::ImageRgb8(buf)
        }
        "RGBA" => {
            let (r, g, b, a) = parse_rgba(color);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgba([r, g, b, a]));
            DynamicImage::ImageRgba8(buf)
        }
        "L" => {
            let l = color.first().copied().unwrap_or(0);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([l]));
            DynamicImage::ImageLuma8(buf)
        }
        "LA" => {
            let l = color.first().copied().unwrap_or(0);
            let a = color.get(1).copied().unwrap_or(255);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::LumaA([l, a]));
            DynamicImage::ImageLumaA8(buf)
        }
        "1" => {
            let v = color.first().copied().unwrap_or(0);
            let pixel = if v != 0 { 255u8 } else { 0u8 };
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([pixel]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(buf),
                mode_override: Some("1"),
                palette: None,
                palette_mode: None,
            });
        }
        "P" => {
            // Palette mode: pixels are indices (0-255); store as Luma8.
            // Palette is empty until putpalette() is called.
            let idx = color.first().copied().unwrap_or(0);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([idx]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(buf),
                mode_override: Some("P"),
                palette: Some(vec![0u8; 256 * 3]),
                palette_mode: Some("RGB".to_string()),
            });
        }
        "PA" => {
            let idx = color.first().copied().unwrap_or(0);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::LumaA([idx, 255]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(buf),
                mode_override: Some("PA"),
                palette: Some(vec![0u8; 256 * 4]),
                palette_mode: Some("RGBA".to_string()),
            });
        }
        // Premultiplied-alpha modes
        "RGBa" => {
            let (r, g, b, a) = parse_rgba(color);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgba([r, g, b, a]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(buf),
                mode_override: Some("RGBa"),
                palette: None,
                palette_mode: None,
            });
        }
        "La" => {
            let l = color.first().copied().unwrap_or(0);
            let a = color.get(1).copied().unwrap_or(255);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::LumaA([l, a]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(buf),
                mode_override: Some("La"),
                palette: None,
                palette_mode: None,
            });
        }
        // RGBX: 4-channel (R, G, B, X), stored as RGBA with X in alpha channel
        "RGBX" => {
            let (r, g, b) = parse_rgb(color);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgba([r, g, b, 0]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(buf),
                mode_override: Some("RGBX"),
                palette: None,
                palette_mode: None,
            });
        }
        // Modes stored as RGB with a mode_override tag (3 channels)
        "YCbCr" | "HSV" | "LAB" => {
            let (r, g, b) = parse_rgb(color);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgb([r, g, b]));
            let m: &'static str = match mode {
                "YCbCr" => "YCbCr",
                "HSV" => "HSV",
                "LAB" => "LAB",
                _ => unreachable!(),
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgb8(buf),
                mode_override: Some(m),
                palette: None,
                palette_mode: None,
            });
        }
        // CMYK: 4-channel, stored as RGBA with mode_override
        "CMYK" => {
            let c = color.first().copied().unwrap_or(0);
            let m_ch = color.get(1).copied().unwrap_or(0);
            let y = color.get(2).copied().unwrap_or(0);
            let k = color.get(3).copied().unwrap_or(0);
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Rgba([c, m_ch, y, k]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(buf),
                mode_override: Some("CMYK"),
                palette: None,
                palette_mode: None,
            });
        }
        // F: 32-bit float, approximated as Luma16 with mode_override
        "F" => {
            let v = color.first().copied().unwrap_or(0) as u16;
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([v]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma16(buf),
                mode_override: Some("F"),
                palette: None,
                palette_mode: None,
            });
        }
        // I: 32-bit signed int, stored as Luma16 (best approximation)
        "I" => {
            let v = color.first().copied().unwrap_or(0) as u16;
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([v]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma16(buf),
                mode_override: Some("I"),
                palette: None,
                palette_mode: None,
            });
        }
        // I;16* variants: 16-bit
        "I;16" | "I;16B" | "I;16L" | "I;16N" => {
            let v = color.first().copied().unwrap_or(0) as u16;
            let buf = ImageBuffer::from_fn(width, height, |_, _| image::Luma([v]));
            let m: &'static str = match mode {
                "I;16" => "I;16",
                "I;16B" => "I;16B",
                "I;16L" => "I;16L",
                "I;16N" => "I;16N",
                _ => unreachable!(),
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma16(buf),
                mode_override: Some(m),
                palette: None,
                palette_mode: None,
            });
        }
        _ => return Err(PilError::UnsupportedMode(mode.to_string())),
    };
    Ok(ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

pub fn save(handle: &ImageHandle, format: &str) -> Result<Vec<u8>> {
    save_with_options(handle, format, None)
}

pub fn save_with_options(
    handle: &ImageHandle,
    format: &str,
    quality: Option<u8>,
) -> Result<Vec<u8>> {
    let mut buf = Cursor::new(Vec::new());
    match format.to_ascii_lowercase().as_str() {
        "jpeg" | "jpg" => {
            let q = quality.unwrap_or(75);
            let rgb = handle.inner.to_rgb8();
            let encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(&mut buf, q);
            rgb.write_with_encoder(encoder)?;
        }
        _ => {
            let fmt = parse_format(format)?;
            handle.inner.write_to(&mut buf, fmt)?;
        }
    }
    Ok(buf.into_inner())
}

// ---------------------------------------------------------------------------
// Properties
// ---------------------------------------------------------------------------

pub fn size(handle: &ImageHandle) -> (u32, u32) {
    handle.inner.dimensions()
}

pub fn mode(handle: &ImageHandle) -> &'static str {
    if let Some(m) = handle.mode_override {
        return m;
    }
    match &handle.inner {
        DynamicImage::ImageLuma8(_) => "L",
        DynamicImage::ImageLumaA8(_) => "LA",
        DynamicImage::ImageRgb8(_) => "RGB",
        DynamicImage::ImageRgba8(_) => "RGBA",
        DynamicImage::ImageLuma16(_) => "I;16",
        DynamicImage::ImageLumaA16(_) => "LA;16",
        DynamicImage::ImageRgb16(_) => "RGB;16",
        DynamicImage::ImageRgba16(_) => "RGBA;16",
        DynamicImage::ImageRgb32F(_) => "RGB;32F",
        DynamicImage::ImageRgba32F(_) => "RGBA;32F",
        _ => "RGB",
    }
}

pub fn tobytes(handle: &ImageHandle) -> Vec<u8> {
    // For big-endian 16-bit modes, byte-swap the raw LE u16 buffer to BE
    if handle.mode_override == Some("I;16B") {
        if let DynamicImage::ImageLuma16(buf) = &handle.inner {
            let mut out = Vec::with_capacity(buf.len() * 2);
            for px in buf.pixels() {
                let v = px.0[0];
                out.extend_from_slice(&v.to_be_bytes());
            }
            return out;
        }
    }
    handle.inner.as_bytes().to_vec()
}

// ---------------------------------------------------------------------------
// Pixel access
// ---------------------------------------------------------------------------

pub fn getpixel(handle: &ImageHandle, x: u32, y: u32) -> [u8; 4] {
    // For 16-bit modes (I, F, I;16*), get_pixel normalises to u8 losing precision.
    // Return the raw low byte of the 16-bit value directly.
    if let DynamicImage::ImageLuma16(buf) = &handle.inner {
        let v = buf.get_pixel(x, y)[0];
        // Return low byte as [v_lo, v_hi, 0, 255] so callers can reconstruct
        return [(v & 0xFF) as u8, ((v >> 8) & 0xFF) as u8, 0, 255];
    }
    let p = handle.inner.get_pixel(x, y);
    p.0
}

pub fn putpixel(handle: &mut ImageHandle, x: u32, y: u32, color: [u8; 4]) {
    // Write in the image's native format to avoid mode corruption
    match &mut handle.inner {
        DynamicImage::ImageLuma8(buf) => {
            buf.put_pixel(x, y, image::Luma([color[0]]));
        }
        DynamicImage::ImageLumaA8(buf) => {
            // color[1] holds the A value when input is an LA tuple (via extract_color_rgba)
            buf.put_pixel(x, y, image::LumaA([color[0], color[1]]));
        }
        DynamicImage::ImageRgb8(buf) => {
            buf.put_pixel(x, y, image::Rgb([color[0], color[1], color[2]]));
        }
        DynamicImage::ImageLuma16(buf) => {
            // Reconstruct u16 from [lo, hi] bytes
            let v = (color[0] as u16) | ((color[1] as u16) << 8);
            buf.put_pixel(x, y, image::Luma([v]));
        }
        _ => {
            handle.inner.put_pixel(x, y, image::Rgba(color));
        }
    }
}

// ---------------------------------------------------------------------------
// Geometric transforms
// ---------------------------------------------------------------------------

pub fn resize(handle: &ImageHandle, w: u32, h: u32, filter: &str) -> ImageHandle {
    let f = parse_filter(filter);

    // For non-nearest filters on alpha-bearing images, use alpha-premultiplied
    // interpolation to avoid colour bleed from transparent pixels.
    if f != image::imageops::FilterType::Nearest {
        if let DynamicImage::ImageRgba8(ref src) = handle.inner {
            return ImageHandle {
                inner: DynamicImage::ImageRgba8(resize_rgba_premult(src, w, h, f)),
                mode_override: handle.mode_override,
                palette: None,
                palette_mode: None,
            };
        }
        if let DynamicImage::ImageLumaA8(ref src) = handle.inner {
            return ImageHandle {
                inner: DynamicImage::ImageLumaA8(resize_lumaa_premult(src, w, h, f)),
                mode_override: handle.mode_override,
                palette: None,
                palette_mode: None,
            };
        }
    }

    ImageHandle {
        inner: handle.inner.resize_exact(w, h, f),
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

fn resize_rgba_premult(
    src: &ImageBuffer<image::Rgba<u8>, Vec<u8>>,
    w: u32,
    h: u32,
    f: image::imageops::FilterType,
) -> ImageBuffer<image::Rgba<u8>, Vec<u8>> {
    let (sw, sh) = src.dimensions();
    // Premultiply alpha
    let mut pm: ImageBuffer<image::Rgba<u8>, Vec<u8>> = ImageBuffer::new(sw, sh);
    for (x, y, p) in src.enumerate_pixels() {
        let image::Rgba([r, g, b, a]) = *p;
        let af = a as f32 / 255.0;
        pm.put_pixel(
            x,
            y,
            image::Rgba([
                (r as f32 * af + 0.5) as u8,
                (g as f32 * af + 0.5) as u8,
                (b as f32 * af + 0.5) as u8,
                a,
            ]),
        );
    }
    // Resize premultiplied image
    let resized = DynamicImage::ImageRgba8(pm).resize_exact(w, h, f);
    // Un-premultiply
    if let DynamicImage::ImageRgba8(ref rb) = resized {
        let mut out: ImageBuffer<image::Rgba<u8>, Vec<u8>> = ImageBuffer::new(w, h);
        for (x, y, p) in rb.enumerate_pixels() {
            let image::Rgba([pr, pg, pb, a]) = *p;
            let (r, g, b) = if a == 0 {
                (0, 0, 0)
            } else {
                let af = a as f32 / 255.0;
                (
                    ((pr as f32 / af + 0.5) as u32).min(255) as u8,
                    ((pg as f32 / af + 0.5) as u32).min(255) as u8,
                    ((pb as f32 / af + 0.5) as u32).min(255) as u8,
                )
            };
            out.put_pixel(x, y, image::Rgba([r, g, b, a]));
        }
        return out;
    }
    // Fallback (shouldn't happen)
    match resized {
        DynamicImage::ImageRgba8(b) => b,
        _ => unreachable!(),
    }
}

fn resize_lumaa_premult(
    src: &ImageBuffer<image::LumaA<u8>, Vec<u8>>,
    w: u32,
    h: u32,
    f: image::imageops::FilterType,
) -> ImageBuffer<image::LumaA<u8>, Vec<u8>> {
    let (sw, sh) = src.dimensions();
    // Premultiply alpha
    let mut pm: ImageBuffer<image::LumaA<u8>, Vec<u8>> = ImageBuffer::new(sw, sh);
    for (x, y, p) in src.enumerate_pixels() {
        let image::LumaA([l, a]) = *p;
        let af = a as f32 / 255.0;
        pm.put_pixel(x, y, image::LumaA([(l as f32 * af + 0.5) as u8, a]));
    }
    // Resize premultiplied image
    let resized = DynamicImage::ImageLumaA8(pm).resize_exact(w, h, f);
    // Un-premultiply
    if let DynamicImage::ImageLumaA8(ref rb) = resized {
        let mut out: ImageBuffer<image::LumaA<u8>, Vec<u8>> = ImageBuffer::new(w, h);
        for (x, y, p) in rb.enumerate_pixels() {
            let image::LumaA([pl, a]) = *p;
            let l = if a == 0 {
                0
            } else {
                let af = a as f32 / 255.0;
                ((pl as f32 / af + 0.5) as u32).min(255) as u8
            };
            out.put_pixel(x, y, image::LumaA([l, a]));
        }
        return out;
    }
    match resized {
        DynamicImage::ImageLumaA8(b) => b,
        _ => unreachable!(),
    }
}

pub fn crop(handle: &ImageHandle, x: u32, y: u32, w: u32, h: u32) -> ImageHandle {
    ImageHandle {
        inner: handle.inner.crop_imm(x, y, w, h),
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

/// Crop with possibly out-of-bounds coordinates; fills any extension with black/transparent.
pub fn crop_oob(handle: &ImageHandle, x0: i32, y0: i32, x1: i32, y1: i32) -> ImageHandle {
    let (sw, sh) = handle.inner.dimensions();
    let out_w = (x1 - x0).max(0) as u32;
    let out_h = (y1 - y0).max(0) as u32;
    if out_w == 0 || out_h == 0 {
        return new_image(mode(handle), out_w, out_h, &[]).unwrap_or_else(|_| ImageHandle {
            inner: DynamicImage::ImageRgba8(image::RgbaImage::new(out_w, out_h)),
            mode_override: None,
            palette: None,
            palette_mode: None,
        });
    }
    // Create destination image in RGBA, then convert back to original mode
    let mut out = image::RgbaImage::new(out_w, out_h);
    for oy in 0..out_h {
        for ox in 0..out_w {
            let sx = ox as i32 + x0;
            let sy = oy as i32 + y0;
            if sx >= 0 && sx < sw as i32 && sy >= 0 && sy < sh as i32 {
                let p = handle.inner.get_pixel(sx as u32, sy as u32);
                out.put_pixel(ox, oy, p);
            }
            // else: pixel stays [0,0,0,0] (transparent black)
        }
    }
    let di = DynamicImage::ImageRgba8(out);
    let result = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(di.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(di.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

pub fn rotate(handle: &ImageHandle, degrees: f32) -> ImageHandle {
    let deg = ((degrees % 360.0) + 360.0) % 360.0;

    // PIL rotates CCW; image crate rotates CW — swap 90↔270
    if (deg - 90.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate270(),
            mode_override: None,
            palette: None,
            palette_mode: None,
        };
    }
    if (deg - 180.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate180(),
            mode_override: None,
            palette: None,
            palette_mode: None,
        };
    }
    if (deg - 270.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate90(),
            mode_override: None,
            palette: None,
            palette_mode: None,
        };
    }
    if deg < 0.5 || (360.0 - deg) < 0.5 {
        return ImageHandle {
            inner: handle.inner.clone(),
            mode_override: None,
            palette: None,
            palette_mode: None,
        };
    }

    // Arbitrary rotation — nearest-neighbor sampling, same output size, black fill
    let (w, h) = handle.inner.dimensions();
    let rad = -degrees.to_radians(); // counter-clockwise like PIL
    let cos = rad.cos();
    let sin = rad.sin();
    let cx = w as f32 / 2.0;
    let cy = h as f32 / 2.0;

    let mut out = DynamicImage::new_rgba8(w, h);
    for oy in 0..h {
        for ox in 0..w {
            let dx = ox as f32 - cx;
            let dy = oy as f32 - cy;
            let sx = (dx * cos - dy * sin + cx).round() as i32;
            let sy = (dx * sin + dy * cos + cy).round() as i32;
            if sx >= 0 && sx < w as i32 && sy >= 0 && sy < h as i32 {
                out.put_pixel(ox, oy, handle.inner.get_pixel(sx as u32, sy as u32));
            }
        }
    }
    // Convert back to original mode so rotation preserves mode
    let out = match mode(handle) {
        "L" => DynamicImage::ImageLuma8(out.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        "RGB" => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out, // RGBA already
    };
    ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Transpose operations matching PIL constants:
/// 0 = FLIP_LEFT_RIGHT, 1 = FLIP_TOP_BOTTOM, 2 = ROTATE_90,
/// 3 = ROTATE_180, 4 = ROTATE_270, 5 = TRANSPOSE, 6 = TRANSVERSE
pub fn transpose(handle: &ImageHandle, method: u8) -> Result<ImageHandle> {
    let img = &handle.inner;
    let out = match method {
        0 => img.fliph(),
        1 => img.flipv(),
        // PIL ROTATE_90 is CCW; image crate rotate90() is CW — swap them
        2 => img.rotate270(),
        3 => img.rotate180(),
        4 => img.rotate90(),
        5 => {
            // TRANSPOSE = mirror along main diagonal: (x,y) → (y,x)
            let rotated = img.rotate90();
            rotated.fliph()
        }
        6 => {
            // TRANSVERSE = mirror along anti-diagonal: (x,y) → (H-1-y, W-1-x)
            let rotated = img.rotate90();
            rotated.flipv()
        }
        _ => {
            return Err(PilError::InvalidOperation(format!(
                "unknown transpose method: {method}"
            )))
        }
    };
    Ok(ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

// ---------------------------------------------------------------------------
// Affine / perspective transform
// ---------------------------------------------------------------------------

/// Apply an affine transform. `data` is [a, b, c, d, e, f] where:
/// source_x = a * out_x + b * out_y + c
/// source_y = d * out_x + e * out_y + f
pub fn transform_affine(
    handle: &ImageHandle,
    out_w: u32,
    out_h: u32,
    data: &[f64; 6],
) -> ImageHandle {
    let (sw, sh) = handle.inner.dimensions();
    let [a, b, c, d, e, f] = *data;
    let src_mode = mode(handle);

    let mut out = DynamicImage::new_rgba8(out_w, out_h);
    for oy in 0..out_h {
        for ox in 0..out_w {
            let sx = (a * ox as f64 + b * oy as f64 + c).round() as i32;
            let sy = (d * ox as f64 + e * oy as f64 + f).round() as i32;
            if sx >= 0 && sx < sw as i32 && sy >= 0 && sy < sh as i32 {
                out.put_pixel(ox, oy, handle.inner.get_pixel(sx as u32, sy as u32));
            }
        }
    }

    let out = match src_mode {
        "L" => DynamicImage::ImageLuma8(out.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        "RGB" => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out,
    };
    ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Apply a perspective transform. `data` is [a, b, c, d, e, f, g, h] where:
/// source_x = (a * out_x + b * out_y + c) / (g * out_x + h * out_y + 1)
/// source_y = (d * out_x + e * out_y + f) / (g * out_x + h * out_y + 1)
pub fn transform_perspective(
    handle: &ImageHandle,
    out_w: u32,
    out_h: u32,
    data: &[f64; 8],
) -> ImageHandle {
    let (sw, sh) = handle.inner.dimensions();
    let src_mode = mode(handle);

    let mut out = DynamicImage::new_rgba8(out_w, out_h);
    for oy in 0..out_h {
        for ox in 0..out_w {
            let denom = data[6] * ox as f64 + data[7] * oy as f64 + 1.0;
            if denom.abs() < 1e-10 {
                continue;
            }
            let sx = ((data[0] * ox as f64 + data[1] * oy as f64 + data[2]) / denom).round() as i32;
            let sy = ((data[3] * ox as f64 + data[4] * oy as f64 + data[5]) / denom).round() as i32;
            if sx >= 0 && sx < sw as i32 && sy >= 0 && sy < sh as i32 {
                out.put_pixel(ox, oy, handle.inner.get_pixel(sx as u32, sy as u32));
            }
        }
    }

    let out = match src_mode {
        "L" => DynamicImage::ImageLuma8(out.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        "RGB" => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out,
    };
    ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Apply a bilinear quad transform. `data` is [a0, a1, a2, a3, b0, b1, b2, b3] where:
/// source_x = a0 + a1*u + a2*v + a3*u*v
/// source_y = b0 + b1*u + b2*v + b3*u*v
/// and u, v are the local pixel coordinates within the output box.
pub fn transform_quad(
    handle: &ImageHandle,
    out_w: u32,
    out_h: u32,
    data: &[f64; 8],
) -> ImageHandle {
    let (sw, sh) = handle.inner.dimensions();
    let src_mode = mode(handle);
    let [a0, a1, a2, a3, b0, b1, b2, b3] = *data;

    let mut out = DynamicImage::new_rgba8(out_w, out_h);
    for oy in 0..out_h {
        let v = oy as f64;
        for ox in 0..out_w {
            let u = ox as f64;
            let sx = (a0 + a1 * u + a2 * v + a3 * u * v).round() as i32;
            let sy = (b0 + b1 * u + b2 * v + b3 * u * v).round() as i32;
            if sx >= 0 && sx < sw as i32 && sy >= 0 && sy < sh as i32 {
                out.put_pixel(ox, oy, handle.inner.get_pixel(sx as u32, sy as u32));
            }
        }
    }

    let out = match src_mode {
        "L" => DynamicImage::ImageLuma8(out.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        "RGB" => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out,
    };
    ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

// ---------------------------------------------------------------------------
// Mode conversion
// ---------------------------------------------------------------------------

/// BT.601 (Pillow-compatible) luma from RGB bytes: r*19595 + g*38470 + b*7471 >> 16
#[inline]
fn bt601_luma(r: u8, g: u8, b: u8) -> u8 {
    let l = (r as u32 * 19595 + g as u32 * 38470 + b as u32 * 7471 + 0x8000) >> 16;
    l as u8
}

pub fn convert(handle: &ImageHandle, target_mode: &str) -> Result<ImageHandle> {
    let (w, h) = handle.inner.dimensions();

    // P/PA mode: must use palette to convert to RGB/RGBA/L
    if matches!(handle.mode_override, Some("P") | Some("PA")) {
        if let Some(pal) = &handle.palette {
            let palette_mode = handle.palette_mode.as_deref().unwrap_or("RGB");
            let stride = if palette_mode == "RGBA" { 4 } else { 3 };
            if let DynamicImage::ImageLuma8(idx_buf) = &handle.inner {
                match target_mode {
                    "RGB" | "RGBA" | "L" | "LA" => {
                        // Map each index through palette
                        let rgb_buf = ImageBuffer::from_fn(w, h, |x, y| {
                            let idx = idx_buf.get_pixel(x, y)[0] as usize;
                            let base = (idx * stride).min(pal.len().saturating_sub(stride));
                            let r = if base < pal.len() { pal[base] } else { 0 };
                            let g = if base + 1 < pal.len() {
                                pal[base + 1]
                            } else {
                                0
                            };
                            let b = if base + 2 < pal.len() {
                                pal[base + 2]
                            } else {
                                0
                            };
                            let a = if stride == 4 && base + 3 < pal.len() {
                                pal[base + 3]
                            } else {
                                255
                            };
                            image::Rgba([r, g, b, a])
                        });
                        let dyn_img = DynamicImage::ImageRgba8(rgb_buf);
                        let result_img = match target_mode {
                            "RGB" => DynamicImage::ImageRgb8(dyn_img.to_rgb8()),
                            "RGBA" => dyn_img,
                            "L" => DynamicImage::ImageLuma8(dyn_img.to_luma8()),
                            "LA" => DynamicImage::ImageLumaA8(dyn_img.to_luma_alpha8()),
                            _ => unreachable!(),
                        };
                        return Ok(ImageHandle {
                            inner: result_img,
                            mode_override: None,
                            palette: None,
                            palette_mode: None,
                        });
                    }
                    "P" => {
                        // Keep as P but maybe different palette — for now just clone
                        return Ok(handle.clone());
                    }
                    _ => {}
                }
            }
        }
    }

    let img = match target_mode {
        "RGB" => DynamicImage::ImageRgb8(handle.inner.to_rgb8()),
        "RGBA" => DynamicImage::ImageRgba8(handle.inner.to_rgba8()),
        "L" => {
            // Use BT.601 coefficients to match Pillow's behavior
            match &handle.inner {
                DynamicImage::ImageLuma8(buf) => DynamicImage::ImageLuma8(buf.clone()),
                DynamicImage::ImageLumaA8(buf) => {
                    let out =
                        ImageBuffer::from_fn(w, h, |x, y| image::Luma([buf.get_pixel(x, y)[0]]));
                    DynamicImage::ImageLuma8(out)
                }
                _ => {
                    let rgba = handle.inner.to_rgba8();
                    let out = ImageBuffer::from_fn(w, h, |x, y| {
                        let p = rgba.get_pixel(x, y);
                        image::Luma([bt601_luma(p[0], p[1], p[2])])
                    });
                    DynamicImage::ImageLuma8(out)
                }
            }
        }
        "LA" => {
            // Use BT.601 coefficients to match Pillow's behavior
            match &handle.inner {
                DynamicImage::ImageLumaA8(buf) => DynamicImage::ImageLumaA8(buf.clone()),
                DynamicImage::ImageLuma8(buf) => {
                    let out = ImageBuffer::from_fn(w, h, |x, y| {
                        image::LumaA([buf.get_pixel(x, y)[0], 255])
                    });
                    DynamicImage::ImageLumaA8(out)
                }
                _ => {
                    let rgba = handle.inner.to_rgba8();
                    let out = ImageBuffer::from_fn(w, h, |x, y| {
                        let p = rgba.get_pixel(x, y);
                        image::LumaA([bt601_luma(p[0], p[1], p[2]), p[3]])
                    });
                    DynamicImage::ImageLumaA8(out)
                }
            }
        }
        "1" => {
            let luma = handle.inner.to_luma8();
            let binary = ImageBuffer::from_fn(w, h, |x, y| {
                let v = luma.get_pixel(x, y)[0];
                image::Luma([if v >= 128 { 255u8 } else { 0u8 }])
            });
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(binary),
                mode_override: Some("1"),
                palette: None,
                palette_mode: None,
            });
        }
        // Premultiplied-alpha modes: store as RGBA/LumaA with mode_override
        // (We handle premultiplication internally in resize; the mode tag lets
        // the Python layer round-trip back correctly.)
        "RGBa" => {
            let rgba = handle.inner.to_rgba8();
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(rgba),
                mode_override: Some("RGBa"),
                palette: None,
                palette_mode: None,
            });
        }
        "La" => {
            let luma_a = handle.inner.to_luma_alpha8();
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(luma_a),
                mode_override: Some("La"),
                palette: None,
                palette_mode: None,
            });
        }
        // ---- P / PA expansion -------------------------------------------
        "P" => {
            // For L-mode sources, use direct mapping: pixel value = palette index.
            // This preserves the exact pixel values as palette indices and creates
            // a standard grayscale palette (matches Pillow's L→P behavior).
            if matches!(mode(handle), "L" | "1") {
                let luma = handle.inner.to_luma8();
                // Grayscale palette: index i → (i, i, i)
                let mut flat_palette = Vec::with_capacity(256 * 3);
                for i in 0u8..=255 {
                    flat_palette.push(i);
                    flat_palette.push(i);
                    flat_palette.push(i);
                }
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageLuma8(luma),
                    mode_override: Some("P"),
                    palette: Some(flat_palette),
                    palette_mode: Some("RGB".to_string()),
                });
            }
            // For other sources, use quantize
            let quantized = quantize(handle, 256)?;
            return Ok(quantized);
        }
        "PA" => {
            // P with alpha channel: quantize then wrap as LumaA8
            let quantized = quantize(handle, 256)?;
            let (qw, qh) = quantized.inner.dimensions();
            let luma = quantized.inner.to_luma8();
            let out =
                ImageBuffer::from_fn(qw, qh, |x, y| image::LumaA([luma.get_pixel(x, y)[0], 255]));
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(out),
                mode_override: Some("PA"),
                palette: quantized.palette,
                palette_mode: quantized.palette_mode,
            });
        }
        _ => {
            // If source is P or PA, expand through palette first
            let src_mode = mode(handle);
            if src_mode == "P" || src_mode == "PA" {
                let expanded = expand_palette(handle)?;
                return convert(&expanded, target_mode);
            }
            // RGBX: 4-channel, stored as RGBA with X = 0 in alpha channel
            if target_mode == "RGBX" {
                let rgba = handle.inner.to_rgba8();
                let (w, h) = rgba.dimensions();
                let out = ImageBuffer::from_fn(w, h, |x, y| {
                    let p = rgba.get_pixel(x, y).0;
                    image::Rgba([p[0], p[1], p[2], 0])
                });
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageRgba8(out),
                    mode_override: Some("RGBX"),
                    palette: None,
                    palette_mode: None,
                });
            }
            // RGB-stored color-space modes: convert via RGB then re-tag
            let m: Option<&'static str> = match target_mode {
                "YCbCr" => Some("YCbCr"),
                "HSV" => Some("HSV"),
                "LAB" => Some("LAB"),
                _ => None,
            };
            if let Some(m) = m {
                let rgb = handle.inner.to_rgb8();
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageRgb8(rgb),
                    mode_override: Some(m),
                    palette: None,
                    palette_mode: None,
                });
            }
            // CMYK: 4-channel stored as RGBA with mode_override
            if target_mode == "CMYK" {
                let rgba = handle.inner.to_rgba8();
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageRgba8(rgba),
                    mode_override: Some("CMYK"),
                    palette: None,
                    palette_mode: None,
                });
            }
            // I: 32-bit signed int, approximated as Luma16
            if target_mode == "I" {
                let (w, h) = handle.inner.dimensions();
                let luma = handle.inner.to_luma8();
                let buf = ImageBuffer::from_fn(w, h, |x, y| {
                    image::Luma([luma.get_pixel(x, y)[0] as u16])
                });
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageLuma16(buf),
                    mode_override: Some("I"),
                    palette: None,
                    palette_mode: None,
                });
            }
            // F: 32-bit float, approximated as Luma16
            if target_mode == "F" {
                let (w, h) = handle.inner.dimensions();
                let luma = handle.inner.to_luma8();
                let buf = ImageBuffer::from_fn(w, h, |x, y| {
                    image::Luma([luma.get_pixel(x, y)[0] as u16])
                });
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageLuma16(buf),
                    mode_override: Some("F"),
                    palette: None,
                    palette_mode: None,
                });
            }
            // I;16 variants
            if matches!(target_mode, "I;16" | "I;16B" | "I;16L" | "I;16N") {
                let (w, h) = handle.inner.dimensions();
                let luma = handle.inner.to_luma8();
                let buf = ImageBuffer::from_fn(w, h, |x, y| {
                    image::Luma([luma.get_pixel(x, y)[0] as u16])
                });
                let m: &'static str = match target_mode {
                    "I;16" => "I;16",
                    "I;16B" => "I;16B",
                    "I;16L" => "I;16L",
                    "I;16N" => "I;16N",
                    _ => unreachable!(),
                };
                return Ok(ImageHandle {
                    inner: DynamicImage::ImageLuma16(buf),
                    mode_override: Some(m),
                    palette: None,
                    palette_mode: None,
                });
            }
            return Err(PilError::UnsupportedMode(target_mode.to_string()));
        }
    };
    Ok(ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

// ---------------------------------------------------------------------------
// Palette helpers
// ---------------------------------------------------------------------------

/// Expand a P/PA image through its stored palette into an RGBA/RGB/L image.
pub fn expand_palette(handle: &ImageHandle) -> Result<ImageHandle> {
    let (w, h) = handle.inner.dimensions();
    let pal = handle.palette.as_deref().unwrap_or(&[]);
    let pal_mode = handle.palette_mode.as_deref().unwrap_or("RGB");
    let stride = if pal_mode == "RGBA" { 4 } else { 3 };

    match mode(handle) {
        "P" => {
            let luma = handle.inner.to_luma8();
            if stride == 4 {
                let out = ImageBuffer::from_fn(w, h, |x, y| {
                    let idx = luma.get_pixel(x, y)[0] as usize;
                    let base = (idx * 4).min(pal.len().saturating_sub(4));
                    image::Rgba([
                        pal.get(base).copied().unwrap_or(0),
                        pal.get(base + 1).copied().unwrap_or(0),
                        pal.get(base + 2).copied().unwrap_or(0),
                        pal.get(base + 3).copied().unwrap_or(255),
                    ])
                });
                Ok(ImageHandle::new(DynamicImage::ImageRgba8(out)))
            } else {
                let out = ImageBuffer::from_fn(w, h, |x, y| {
                    let idx = luma.get_pixel(x, y)[0] as usize;
                    let base = (idx * 3).min(pal.len().saturating_sub(3));
                    image::Rgb([
                        pal.get(base).copied().unwrap_or(0),
                        pal.get(base + 1).copied().unwrap_or(0),
                        pal.get(base + 2).copied().unwrap_or(0),
                    ])
                });
                Ok(ImageHandle::new(DynamicImage::ImageRgb8(out)))
            }
        }
        "PA" => {
            let luma_a = handle.inner.to_luma_alpha8();
            let out = ImageBuffer::from_fn(w, h, |x, y| {
                let px = luma_a.get_pixel(x, y);
                let idx = px[0] as usize;
                let pix_alpha = px[1];
                let base = (idx * stride).min(pal.len().saturating_sub(stride));
                let pal_alpha = if stride == 4 {
                    pal.get(base + 3).copied().unwrap_or(255)
                } else {
                    255
                };
                image::Rgba([
                    pal.get(base).copied().unwrap_or(0),
                    pal.get(base + 1).copied().unwrap_or(0),
                    pal.get(base + 2).copied().unwrap_or(0),
                    ((pix_alpha as u16 * pal_alpha as u16) / 255) as u8,
                ])
            });
            Ok(ImageHandle::new(DynamicImage::ImageRgba8(out)))
        }
        _ => Err(PilError::InvalidOperation(
            "expand_palette: not a palette image".into(),
        )),
    }
}

/// Return the stored palette bytes, optionally re-encoded for `rawmode`.
/// rawmode can be "RGB" (3 bytes/entry) or "RGBA" (4 bytes/entry).
pub fn getpalette(handle: &ImageHandle, rawmode: &str) -> Result<Vec<u8>> {
    let pal = handle
        .palette
        .as_deref()
        .ok_or_else(|| PilError::InvalidOperation("image has no palette".into()))?;
    let pal_mode = handle.palette_mode.as_deref().unwrap_or("RGB");
    let src_stride = if pal_mode == "RGBA" { 4 } else { 3 };
    let dst_stride = if rawmode == "RGBA" { 4 } else { 3 };
    let n_entries = pal.len() / src_stride;
    let mut out = Vec::with_capacity(n_entries * dst_stride);
    for i in 0..n_entries {
        let base = i * src_stride;
        let r = pal.get(base).copied().unwrap_or(0);
        let g = pal.get(base + 1).copied().unwrap_or(0);
        let b = pal.get(base + 2).copied().unwrap_or(0);
        let a = if src_stride == 4 {
            pal.get(base + 3).copied().unwrap_or(255)
        } else {
            255
        };
        out.push(r);
        out.push(g);
        out.push(b);
        if dst_stride == 4 {
            out.push(a);
        }
    }
    Ok(out)
}

pub fn getpalettemode(handle: &ImageHandle) -> Result<String> {
    handle
        .palette_mode
        .clone()
        .ok_or_else(|| PilError::InvalidOperation("image has no palette".into()))
}

/// Store palette bytes on the handle.
/// `data_mode` is the mode of the incoming bytes (e.g. "RGB", "RGBA").
/// Stores exactly the entries provided (up to 256), without padding.
pub fn putpalette(handle: &mut ImageHandle, data: &[u8], data_mode: &str) {
    let stride = if data_mode == "RGBA" { 4 } else { 3 };
    let n = (data.len() / stride).min(256);
    // Store exactly n entries — do NOT pad to 256
    let pal = data[..n * stride].to_vec();
    handle.palette = Some(pal);
    handle.palette_mode = Some(data_mode.to_string());
}

pub fn putpalettealpha(handle: &mut ImageHandle, index: usize, alpha: u8) -> Result<()> {
    let stride = if handle.palette_mode.as_deref() == Some("RGBA") {
        4
    } else {
        3
    };
    let pal = handle
        .palette
        .get_or_insert_with(|| vec![0u8; 256 * stride]);
    // If palette is RGB (3-byte), upgrade to RGBA (4-byte) preserving actual entry count
    if stride == 3 {
        let n_entries = pal.len() / 3;
        let mut rgba_pal = vec![255u8; n_entries * 4];
        for i in 0..n_entries {
            rgba_pal[i * 4] = pal.get(i * 3).copied().unwrap_or(0);
            rgba_pal[i * 4 + 1] = pal.get(i * 3 + 1).copied().unwrap_or(0);
            rgba_pal[i * 4 + 2] = pal.get(i * 3 + 2).copied().unwrap_or(0);
        }
        *pal = rgba_pal;
        handle.palette_mode = Some("RGBA".to_string());
    }
    let pal = handle.palette.as_mut().unwrap();
    let needed = index * 4 + 4;
    if needed > pal.len() {
        pal.resize(needed, 255);
    }
    pal[index * 4 + 3] = alpha;
    Ok(())
}

pub fn putpalettealphas(handle: &mut ImageHandle, alphas: &[u8]) -> Result<()> {
    let stride = if handle.palette_mode.as_deref() == Some("RGBA") {
        4
    } else {
        3
    };
    let pal = handle
        .palette
        .get_or_insert_with(|| vec![0u8; 256 * stride]);
    // Upgrade to RGBA if needed, preserving actual entry count
    if stride == 3 {
        let n_entries = pal.len() / 3;
        let mut rgba_pal = vec![255u8; n_entries * 4];
        for i in 0..n_entries {
            rgba_pal[i * 4] = pal.get(i * 3).copied().unwrap_or(0);
            rgba_pal[i * 4 + 1] = pal.get(i * 3 + 1).copied().unwrap_or(0);
            rgba_pal[i * 4 + 2] = pal.get(i * 3 + 2).copied().unwrap_or(0);
        }
        *pal = rgba_pal;
        handle.palette_mode = Some("RGBA".to_string());
    }
    let pal = handle.palette.as_mut().unwrap();
    let n_alphas = alphas.len().min(256);
    let needed = n_alphas * 4;
    if needed > pal.len() {
        pal.resize(needed, 255);
    }
    for (i, &a) in alphas.iter().enumerate().take(n_alphas) {
        pal[i * 4 + 3] = a;
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------

pub fn filter(handle: &ImageHandle, name: &str, args: &[f32]) -> Result<ImageHandle> {
    let out = match name {
        "blur" => {
            let sigma = args.first().copied().unwrap_or(1.0);
            handle.inner.blur(sigma)
        }
        "gaussian_blur" => {
            let sigma = args.first().copied().unwrap_or(2.0);
            handle.inner.blur(sigma)
        }
        "sharpen" => handle.inner.unsharpen(3.0, 1),
        "smooth" => handle.inner.blur(0.5),
        "smooth_more" => handle.inner.blur(1.0),
        "contour" => {
            // Pillow CONTOUR: edge detection then invert
            #[rustfmt::skip]
            let k: [f32; 9] = [
                -1.0, -1.0, -1.0,
                -1.0,  8.0, -1.0,
                -1.0, -1.0, -1.0,
            ];
            apply_kernel3x3(&handle.inner, &k)
        }
        "detail" => {
            // Pillow DETAIL kernel (scale=6, offset=0)
            #[rustfmt::skip]
            let k: [f32; 9] = [
                 0.0, -1.0,  0.0,
                -1.0, 10.0, -1.0,
                 0.0, -1.0,  0.0,
            ];
            apply_kernel3x3_scaled(&handle.inner, &k, 6.0, 0.0)
        }
        "edge_enhance" => {
            // Pillow EDGE_ENHANCE (scale=2, offset=0)
            #[rustfmt::skip]
            let k: [f32; 9] = [
                -1.0, -1.0, -1.0,
                -1.0, 10.0, -1.0,
                -1.0, -1.0, -1.0,
            ];
            apply_kernel3x3_scaled(&handle.inner, &k, 2.0, 0.0)
        }
        "edge_enhance_more" => {
            // Pillow EDGE_ENHANCE_MORE (scale=1, offset=0)
            #[rustfmt::skip]
            let k: [f32; 9] = [
                -1.0, -1.0, -1.0,
                -1.0,  9.0, -1.0,
                -1.0, -1.0, -1.0,
            ];
            apply_kernel3x3(&handle.inner, &k)
        }
        "emboss" => {
            // Pillow EMBOSS (scale=1, offset=128)
            #[rustfmt::skip]
            let k: [f32; 9] = [
                -1.0, -1.0,  0.0,
                -1.0,  0.0,  1.0,
                 0.0,  1.0,  1.0,
            ];
            apply_kernel3x3_scaled(&handle.inner, &k, 1.0, 128.0)
        }
        "find_edges" => {
            // Pillow FIND_EDGES (scale=1, offset=0)
            #[rustfmt::skip]
            let k: [f32; 9] = [
                -1.0, -1.0, -1.0,
                -1.0,  8.0, -1.0,
                -1.0, -1.0, -1.0,
            ];
            apply_kernel3x3(&handle.inner, &k)
        }
        "kernel3x3" => {
            // Custom 3x3 kernel: args = [k0..k8, scale, offset]
            if args.len() < 9 {
                return Err(PilError::InvalidOperation(
                    "kernel3x3 requires 9+ args".into(),
                ));
            }
            let k: [f32; 9] = [
                args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8],
            ];
            let scale = if args.len() > 9 { args[9] } else { 1.0 };
            let offset = if args.len() > 10 { args[10] } else { 0.0 };
            apply_kernel3x3_scaled(&handle.inner, &k, scale, offset)
        }
        "unsharp_mask" => {
            let radius = args.first().copied().unwrap_or(2.0);
            let percent = if args.len() > 1 { args[1] as i32 } else { 150 };
            let _threshold = if args.len() > 2 { args[2] as u8 } else { 3 };
            handle.inner.unsharpen(radius, percent)
        }
        "median" => {
            // Median filter: take middle value in NxN neighborhood
            let size = args.first().copied().unwrap_or(3.0) as u32;
            apply_rank_filter(&handle.inner, size, (size * size) / 2)
        }
        "min_filter" => {
            let size = args.first().copied().unwrap_or(3.0) as u32;
            apply_rank_filter(&handle.inner, size, 0)
        }
        "max_filter" => {
            let size = args.first().copied().unwrap_or(3.0) as u32;
            apply_rank_filter(&handle.inner, size, size * size - 1)
        }
        "box_blur" => {
            let radius = args.first().copied().unwrap_or(1.0) as u32;
            apply_box_blur(&handle.inner, radius)
        }
        _ => {
            return Err(PilError::InvalidOperation(format!(
                "unknown filter: {name}"
            )))
        }
    };
    Ok(ImageHandle {
        inner: out,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

fn apply_kernel3x3(img: &image::DynamicImage, kernel: &[f32; 9]) -> image::DynamicImage {
    apply_kernel3x3_scaled(img, kernel, 1.0, 0.0)
}

fn apply_kernel3x3_scaled(
    img: &image::DynamicImage,
    kernel: &[f32; 9],
    scale: f32,
    offset: f32,
) -> image::DynamicImage {
    let inv_scale = 1.0 / scale;

    // Preserve L mode
    if matches!(img, image::DynamicImage::ImageLuma8(_)) {
        let gray = img.to_luma8();
        let (w, h) = gray.dimensions();
        let mut out = image::GrayImage::new(w, h);
        for y in 0..h {
            for x in 0..w {
                let mut sum = 0.0f32;
                let mut ki = 0;
                for ky in -1i32..=1 {
                    for kx in -1i32..=1 {
                        let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                        let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                        sum += gray.get_pixel(sx, sy)[0] as f32 * kernel[ki];
                        ki += 1;
                    }
                }
                let v = (sum * inv_scale + offset).clamp(0.0, 255.0) as u8;
                out.put_pixel(x, y, image::Luma([v]));
            }
        }
        return image::DynamicImage::ImageLuma8(out);
    }

    let is_rgb = matches!(img, image::DynamicImage::ImageRgb8(_));
    let rgba = img.to_rgba8();
    let (w, h) = rgba.dimensions();
    let mut out = image::RgbaImage::new(w, h);

    for y in 0..h {
        for x in 0..w {
            let mut r_sum = 0.0f32;
            let mut g_sum = 0.0f32;
            let mut b_sum = 0.0f32;
            let mut ki = 0;
            for ky in -1i32..=1 {
                for kx in -1i32..=1 {
                    let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                    let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                    let p = rgba.get_pixel(sx, sy);
                    r_sum += p[0] as f32 * kernel[ki];
                    g_sum += p[1] as f32 * kernel[ki];
                    b_sum += p[2] as f32 * kernel[ki];
                    ki += 1;
                }
            }
            let a = rgba.get_pixel(x, y)[3];
            let r = (r_sum * inv_scale + offset).clamp(0.0, 255.0) as u8;
            let g = (g_sum * inv_scale + offset).clamp(0.0, 255.0) as u8;
            let b = (b_sum * inv_scale + offset).clamp(0.0, 255.0) as u8;
            out.put_pixel(x, y, image::Rgba([r, g, b, a]));
        }
    }
    if is_rgb {
        // Convert back to RGB to preserve mode
        let rgb = image::RgbImage::from_fn(w, h, |x, y| {
            let p = out.get_pixel(x, y);
            image::Rgb([p[0], p[1], p[2]])
        });
        image::DynamicImage::ImageRgb8(rgb)
    } else {
        image::DynamicImage::ImageRgba8(out)
    }
}

/// Apply an arbitrary NxM kernel: kernel is row-major, kw*kh elements.
pub fn apply_kernel(
    handle: &ImageHandle,
    kw: u32,
    kh: u32,
    kernel: &[f64],
    scale: f64,
    offset: f64,
) -> ImageHandle {
    let kf: Vec<f32> = kernel.iter().map(|&v| v as f32).collect();
    let scale_f = scale as f32;
    let offset_f = offset as f32;
    let half_x = (kw / 2) as i32;
    let half_y = (kh / 2) as i32;
    let inv_scale = if scale_f == 0.0 { 1.0 } else { 1.0 / scale_f };

    let is_luma = matches!(handle.inner, DynamicImage::ImageLuma8(_));
    let is_rgb = matches!(handle.inner, DynamicImage::ImageRgb8(_));

    let (w, h) = handle.inner.dimensions();

    if is_luma {
        let gray = handle.inner.to_luma8();
        let mut out = image::GrayImage::new(w, h);
        for y in 0..h {
            for x in 0..w {
                let mut sum = 0.0f32;
                for ky in 0..kh as i32 {
                    for kx in 0..kw as i32 {
                        let sx = (x as i32 + kx - half_x).clamp(0, w as i32 - 1) as u32;
                        let sy = (y as i32 + ky - half_y).clamp(0, h as i32 - 1) as u32;
                        let ki = (ky * kw as i32 + kx) as usize;
                        sum +=
                            gray.get_pixel(sx, sy)[0] as f32 * kf.get(ki).copied().unwrap_or(0.0);
                    }
                }
                let v = (sum * inv_scale + offset_f).clamp(0.0, 255.0) as u8;
                out.put_pixel(x, y, image::Luma([v]));
            }
        }
        return ImageHandle {
            inner: DynamicImage::ImageLuma8(out),
            mode_override: handle.mode_override,
            palette: None,
            palette_mode: None,
        };
    }

    let rgba = handle.inner.to_rgba8();
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let mut rs = 0.0f32;
            let mut gs = 0.0f32;
            let mut bs = 0.0f32;
            for ky in 0..kh as i32 {
                for kx in 0..kw as i32 {
                    let sx = (x as i32 + kx - half_x).clamp(0, w as i32 - 1) as u32;
                    let sy = (y as i32 + ky - half_y).clamp(0, h as i32 - 1) as u32;
                    let ki = (ky * kw as i32 + kx) as usize;
                    let k = kf.get(ki).copied().unwrap_or(0.0);
                    let p = rgba.get_pixel(sx, sy);
                    rs += p[0] as f32 * k;
                    gs += p[1] as f32 * k;
                    bs += p[2] as f32 * k;
                }
            }
            let a = rgba.get_pixel(x, y)[3];
            let r = (rs * inv_scale + offset_f).clamp(0.0, 255.0) as u8;
            let g = (gs * inv_scale + offset_f).clamp(0.0, 255.0) as u8;
            let b = (bs * inv_scale + offset_f).clamp(0.0, 255.0) as u8;
            out.put_pixel(x, y, image::Rgba([r, g, b, a]));
        }
    }
    let result = if is_rgb {
        DynamicImage::ImageRgb8(DynamicImage::ImageRgba8(out).to_rgb8())
    } else {
        DynamicImage::ImageRgba8(out)
    };
    ImageHandle {
        inner: result,
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

fn apply_rank_filter(img: &image::DynamicImage, size: u32, rank: u32) -> image::DynamicImage {
    let half = (size / 2) as i32;
    let rank = rank as usize;

    // Preserve L mode
    if matches!(img, image::DynamicImage::ImageLuma8(_)) {
        let gray = img.to_luma8();
        let (w, h) = gray.dimensions();
        let mut out = image::GrayImage::new(w, h);
        for y in 0..h {
            for x in 0..w {
                let mut vals: Vec<u8> = Vec::new();
                for ky in -half..=half {
                    for kx in -half..=half {
                        let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                        let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                        vals.push(gray.get_pixel(sx, sy)[0]);
                    }
                }
                vals.sort_unstable();
                let idx = rank.min(vals.len() - 1);
                out.put_pixel(x, y, image::Luma([vals[idx]]));
            }
        }
        return image::DynamicImage::ImageLuma8(out);
    }

    let rgba = img.to_rgba8();
    let (w, h) = rgba.dimensions();
    let mut out = image::RgbaImage::new(w, h);

    for y in 0..h {
        for x in 0..w {
            let mut rs: Vec<u8> = Vec::new();
            let mut gs: Vec<u8> = Vec::new();
            let mut bs: Vec<u8> = Vec::new();
            for ky in -half..=half {
                for kx in -half..=half {
                    let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                    let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                    let p = rgba.get_pixel(sx, sy);
                    rs.push(p[0]);
                    gs.push(p[1]);
                    bs.push(p[2]);
                }
            }
            rs.sort_unstable();
            gs.sort_unstable();
            bs.sort_unstable();
            let idx = rank.min(rs.len() - 1);
            let a = rgba.get_pixel(x, y)[3];
            out.put_pixel(x, y, image::Rgba([rs[idx], gs[idx], bs[idx], a]));
        }
    }
    image::DynamicImage::ImageRgba8(out)
}

fn apply_box_blur(img: &image::DynamicImage, radius: u32) -> image::DynamicImage {
    if radius == 0 {
        return img.clone();
    }
    let size = 2 * radius + 1;
    let half = radius as i32;

    // Preserve L mode
    if matches!(img, image::DynamicImage::ImageLuma8(_)) {
        let gray = img.to_luma8();
        let (w, h) = gray.dimensions();
        let mut out = image::GrayImage::new(w, h);
        let n = (size * size) as f32;
        for y in 0..h {
            for x in 0..w {
                let mut sum = 0.0f32;
                for ky in -half..=half {
                    for kx in -half..=half {
                        let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                        let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                        sum += gray.get_pixel(sx, sy)[0] as f32;
                    }
                }
                out.put_pixel(x, y, image::Luma([(sum / n) as u8]));
            }
        }
        return image::DynamicImage::ImageLuma8(out);
    }

    // Preserve RGB mode
    if matches!(img, image::DynamicImage::ImageRgb8(_)) {
        let rgb = img.to_rgb8();
        let (w, h) = rgb.dimensions();
        let mut out = image::RgbImage::new(w, h);
        let n = (size * size) as f32;
        for y in 0..h {
            for x in 0..w {
                let mut r_sum = 0.0f32;
                let mut g_sum = 0.0f32;
                let mut b_sum = 0.0f32;
                for ky in -half..=half {
                    for kx in -half..=half {
                        let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                        let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                        let p = rgb.get_pixel(sx, sy);
                        r_sum += p[0] as f32;
                        g_sum += p[1] as f32;
                        b_sum += p[2] as f32;
                    }
                }
                out.put_pixel(
                    x,
                    y,
                    image::Rgb([(r_sum / n) as u8, (g_sum / n) as u8, (b_sum / n) as u8]),
                );
            }
        }
        return image::DynamicImage::ImageRgb8(out);
    }

    let rgba = img.to_rgba8();
    let (w, h) = rgba.dimensions();
    let mut out = image::RgbaImage::new(w, h);
    let n = (size * size) as f32;
    for y in 0..h {
        for x in 0..w {
            let mut r_sum = 0.0f32;
            let mut g_sum = 0.0f32;
            let mut b_sum = 0.0f32;
            for ky in -half..=half {
                for kx in -half..=half {
                    let sx = (x as i32 + kx).clamp(0, w as i32 - 1) as u32;
                    let sy = (y as i32 + ky).clamp(0, h as i32 - 1) as u32;
                    let p = rgba.get_pixel(sx, sy);
                    r_sum += p[0] as f32;
                    g_sum += p[1] as f32;
                    b_sum += p[2] as f32;
                }
            }
            let a = rgba.get_pixel(x, y)[3];
            out.put_pixel(
                x,
                y,
                image::Rgba([(r_sum / n) as u8, (g_sum / n) as u8, (b_sum / n) as u8, a]),
            );
        }
    }
    image::DynamicImage::ImageRgba8(out)
}

// ---------------------------------------------------------------------------
// Drawing
// ---------------------------------------------------------------------------

/// Convert a draw color `[R, G, B, A]` to the correct `image::Rgba` pixel
/// for the target image mode.
///
/// For `L` images the Python layer already expands a scalar to `(v, v, v)`,
/// so `[R, G, B, A]` arrives with R==G==B and we pass them straight through
/// (the `image` crate converts Rgba → Luma via standard luminance).
///
/// For `LA` images the Python layer passes the LA pair as `[L, A, 0, 255]`
/// from `extract_color_rgba`.  We must expand L to all three channels and
/// keep A, otherwise `image`'s Rgba→LumaA conversion applies the luminance
/// formula and distorts the stored value.
fn color_to_pixel(handle: &ImageHandle, color: [u8; 4]) -> image::Rgba<u8> {
    match &handle.inner {
        DynamicImage::ImageLumaA8(_) => {
            // color = [R, G, B, A] from extract_rgba; R is L, A is alpha
            image::Rgba([color[0], color[0], color[0], color[3]])
        }
        DynamicImage::ImageLuma8(_) => {
            // color[0] = L (already expanded by Python layer)
            image::Rgba([color[0], color[0], color[0], 255])
        }
        _ => image::Rgba(color),
    }
}

pub fn draw_rectangle(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    color: [u8; 4],
    fill: bool,
) {
    let (w, h) = handle.inner.dimensions();
    let min_x = x0.max(0) as u32;
    let min_y = y0.max(0) as u32;
    let max_x = (x1 as u32).min(w.saturating_sub(1));
    let max_y = (y1 as u32).min(h.saturating_sub(1));
    let pixel = color_to_pixel(handle, color);

    if fill {
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                handle.inner.put_pixel(x, y, pixel);
            }
        }
    } else {
        // Top and bottom edges
        for x in min_x..=max_x {
            if (y0 as u32) < h {
                handle.inner.put_pixel(x, y0 as u32, pixel);
            }
            if (y1 as u32) < h {
                handle.inner.put_pixel(x, y1 as u32, pixel);
            }
        }
        // Left and right edges
        for y in min_y..=max_y {
            if (x0 as u32) < w {
                handle.inner.put_pixel(x0 as u32, y, pixel);
            }
            if (x1 as u32) < w {
                handle.inner.put_pixel(x1 as u32, y, pixel);
            }
        }
    }
}

pub fn draw_line(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    color: [u8; 4],
    width: u32,
) {
    let (w, h) = handle.inner.dimensions();
    let pixel = color_to_pixel(handle, color);
    let half = width as i32 / 2;

    // Bresenham's line algorithm
    let dx = (x1 - x0).abs();
    let dy = -(y1 - y0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx + dy;
    let mut cx = x0;
    let mut cy = y0;

    loop {
        // Draw a square brush at each point for width > 1
        for by in -half..=half {
            for bx in -half..=half {
                let px = cx + bx;
                let py = cy + by;
                if px >= 0 && px < w as i32 && py >= 0 && py < h as i32 {
                    handle.inner.put_pixel(px as u32, py as u32, pixel);
                }
            }
        }

        if cx == x1 && cy == y1 {
            break;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            cx += sx;
        }
        if e2 <= dx {
            err += dx;
            cy += sy;
        }
    }
}

pub fn draw_ellipse(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    color: [u8; 4],
    fill: bool,
) {
    let (w, h) = handle.inner.dimensions();
    let pixel = color_to_pixel(handle, color);
    let cx = (x0 + x1) as f64 / 2.0;
    let cy = (y0 + y1) as f64 / 2.0;
    let rx = (x1 - x0) as f64 / 2.0;
    let ry = (y1 - y0) as f64 / 2.0;
    if rx <= 0.0 || ry <= 0.0 {
        return;
    }

    let min_y = y0.max(0) as u32;
    let max_y = (y1 as u32).min(h.saturating_sub(1));
    let min_x = x0.max(0) as u32;
    let max_x = (x1 as u32).min(w.saturating_sub(1));

    if fill {
        for py in min_y..=max_y {
            for px in min_x..=max_x {
                let dx = (px as f64 - cx) / rx;
                let dy = (py as f64 - cy) / ry;
                if dx * dx + dy * dy <= 1.0 {
                    handle.inner.put_pixel(px, py, pixel);
                }
            }
        }
    } else {
        // Draw outline: check if point is near the ellipse boundary
        for py in min_y..=max_y {
            for px in min_x..=max_x {
                let dx = (px as f64 - cx) / rx;
                let dy = (py as f64 - cy) / ry;
                let d = dx * dx + dy * dy;
                // Check neighbours to see if we're on the boundary
                let dx1 = ((px as f64 + 1.0) - cx) / rx;
                let dy1 = ((py as f64 + 1.0) - cy) / ry;
                let dx0 = ((px as f64 - 1.0) - cx) / rx;
                let dy0 = ((py as f64 - 1.0) - cy) / ry;
                let d_right = dx1 * dx1 + dy * dy;
                let d_down = dx * dx + dy1 * dy1;
                let d_left = dx0 * dx0 + dy * dy;
                let d_up = dx * dx + dy0 * dy0;
                // On boundary if this pixel is inside/on and a neighbour is outside, or vice versa
                if d <= 1.0 && (d_right > 1.0 || d_down > 1.0 || d_left > 1.0 || d_up > 1.0) {
                    handle.inner.put_pixel(px, py, pixel);
                }
            }
        }
    }
}

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

    if fill {
        let pixel = color_to_pixel(handle, color);
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

// ---------------------------------------------------------------------------
// Arc / chord / pieslice
// ---------------------------------------------------------------------------
//
// Angles are in degrees, measured clockwise from 3 o'clock (positive x-axis),
// matching Pillow's convention (y increases downward).

/// Compute arc sample points on the ellipse for the angle range [start, end].
/// Returns enough points for a smooth curve (≥ 1 step per pixel of arc length).
fn arc_points(cx: f64, cy: f64, rx: f64, ry: f64, start: f64, end: f64) -> Vec<(i32, i32)> {
    use std::f64::consts::PI;
    let angle_range = end - start;
    if angle_range <= 0.0 {
        return Vec::new();
    }
    // Approximate arc length to decide step count
    let circumference = PI * (rx + ry); // Ramanujan approximation for full ellipse
    let full_steps = (circumference as usize).max(4);
    let steps = ((full_steps as f64 * angle_range / 360.0) as usize).max(1);
    (0..=steps)
        .map(|i| {
            let a = (start + i as f64 * angle_range / steps as f64) * PI / 180.0;
            let px = (cx + rx * a.cos()).round() as i32;
            let py = (cy + ry * a.sin()).round() as i32;
            (px, py)
        })
        .collect()
}

/// Draw an arc (portion of an ellipse outline) from `start` to `end` degrees.
///
/// Angles increase clockwise; 0° is 3 o'clock.  If `end <= start` the arc
/// wraps around (360° is added to `end`).
#[allow(clippy::too_many_arguments)]
pub fn draw_arc(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    start: f64,
    mut end: f64,
    color: [u8; 4],
) {
    let cx = (x0 + x1) as f64 / 2.0;
    let cy = (y0 + y1) as f64 / 2.0;
    let rx = (x1 - x0) as f64 / 2.0;
    let ry = (y1 - y0) as f64 / 2.0;
    if rx <= 0.0 || ry <= 0.0 {
        return;
    }
    if end <= start {
        end += 360.0;
    }
    let pts = arc_points(cx, cy, rx, ry, start, end);
    for w in pts.windows(2) {
        draw_line(handle, w[0].0, w[0].1, w[1].0, w[1].1, color, 1);
    }
}

/// Draw a chord: the region bounded by an arc and the straight line connecting
/// its endpoints.  `fill=true` fills the region; `fill=false` draws the outline.
#[allow(clippy::too_many_arguments)]
pub fn draw_chord(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    start: f64,
    mut end: f64,
    color: [u8; 4],
    fill: bool,
) {
    let cx = (x0 + x1) as f64 / 2.0;
    let cy = (y0 + y1) as f64 / 2.0;
    let rx = (x1 - x0) as f64 / 2.0;
    let ry = (y1 - y0) as f64 / 2.0;
    if rx <= 0.0 || ry <= 0.0 {
        return;
    }
    if end <= start {
        end += 360.0;
    }
    let pts = arc_points(cx, cy, rx, ry, start, end);
    if fill {
        // Polygon from arc points (closing segment is implicit in draw_polygon)
        let flat: Vec<i32> = pts.iter().flat_map(|(x, y)| [*x, *y]).collect();
        draw_polygon(handle, &flat, color, true);
    } else {
        // Arc outline + chord closing line
        for w in pts.windows(2) {
            draw_line(handle, w[0].0, w[0].1, w[1].0, w[1].1, color, 1);
        }
        if let (Some(first), Some(last)) = (pts.first(), pts.last()) {
            draw_line(handle, last.0, last.1, first.0, first.1, color, 1);
        }
    }
}

/// Draw a pieslice: the region bounded by an arc and two radial lines to the
/// ellipse centre.  `fill=true` fills the region; `fill=false` draws the outline.
#[allow(clippy::too_many_arguments)]
pub fn draw_pieslice(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    start: f64,
    mut end: f64,
    color: [u8; 4],
    fill: bool,
) {
    let cx = (x0 + x1) as f64 / 2.0;
    let cy = (y0 + y1) as f64 / 2.0;
    let rx = (x1 - x0) as f64 / 2.0;
    let ry = (y1 - y0) as f64 / 2.0;
    if rx <= 0.0 || ry <= 0.0 {
        return;
    }
    if end <= start {
        end += 360.0;
    }
    let cx_i = cx.round() as i32;
    let cy_i = cy.round() as i32;
    let pts = arc_points(cx, cy, rx, ry, start, end);
    if fill {
        // Polygon: centre point + arc points
        let mut flat = vec![cx_i, cy_i];
        for (x, y) in &pts {
            flat.push(*x);
            flat.push(*y);
        }
        draw_polygon(handle, &flat, color, true);
    } else {
        // Arc outline + two radial lines from centre (unless full circle)
        let is_full_circle = (end - start) >= 359.9;
        for w in pts.windows(2) {
            draw_line(handle, w[0].0, w[0].1, w[1].0, w[1].1, color, 1);
        }
        if !is_full_circle {
            if let Some(first) = pts.first() {
                draw_line(handle, cx_i, cy_i, first.0, first.1, color, 1);
            }
            if let Some(last) = pts.last() {
                draw_line(handle, cx_i, cy_i, last.0, last.1, color, 1);
            }
        }
    }
}

/// 8×16 monospace bitmap font covering ASCII 32–126 (95 glyphs).
/// Each glyph is 16 bytes (one byte per row, 8 pixels wide).
#[rustfmt::skip]
static FONT_8X16: [u8; 1520] = [
    // 32 ' ' (space)
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 33 '!'
    0x00,0x00,0x18,0x3C,0x3C,0x3C,0x18,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00,
    // 34 '"'
    0x00,0x66,0x66,0x66,0x24,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 35 '#'
    0x00,0x00,0x00,0x6C,0x6C,0xFE,0x6C,0x6C,0x6C,0xFE,0x6C,0x6C,0x00,0x00,0x00,0x00,
    // 36 '$'
    0x18,0x18,0x7C,0xC6,0xC2,0xC0,0x7C,0x06,0x06,0x86,0xC6,0x7C,0x18,0x18,0x00,0x00,
    // 37 '%'
    0x00,0x00,0x00,0x00,0xC2,0xC6,0x0C,0x18,0x30,0x60,0xC6,0x86,0x00,0x00,0x00,0x00,
    // 38 '&'
    0x00,0x00,0x38,0x6C,0x6C,0x38,0x76,0xDC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00,
    // 39 "'"
    0x00,0x30,0x30,0x30,0x60,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 40 '('
    0x00,0x00,0x0C,0x18,0x30,0x30,0x30,0x30,0x30,0x30,0x18,0x0C,0x00,0x00,0x00,0x00,
    // 41 ')'
    0x00,0x00,0x30,0x18,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x18,0x30,0x00,0x00,0x00,0x00,
    // 42 '*'
    0x00,0x00,0x00,0x00,0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00,0x00,0x00,0x00,0x00,
    // 43 '+'
    0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00,0x00,0x00,0x00,0x00,
    // 44 ','
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x18,0x30,0x00,0x00,0x00,
    // 45 '-'
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFE,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 46 '.'
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,
    // 47 '/'
    0x00,0x00,0x00,0x00,0x02,0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00,0x00,0x00,0x00,
    // 48 '0'
    0x00,0x00,0x7C,0xC6,0xC6,0xCE,0xDE,0xF6,0xE6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 49 '1'
    0x00,0x00,0x18,0x38,0x78,0x18,0x18,0x18,0x18,0x18,0x18,0x7E,0x00,0x00,0x00,0x00,
    // 50 '2'
    0x00,0x00,0x7C,0xC6,0x06,0x0C,0x18,0x30,0x60,0xC0,0xC6,0xFE,0x00,0x00,0x00,0x00,
    // 51 '3'
    0x00,0x00,0x7C,0xC6,0x06,0x06,0x3C,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 52 '4'
    0x00,0x00,0x0C,0x1C,0x3C,0x6C,0xCC,0xFE,0x0C,0x0C,0x0C,0x1E,0x00,0x00,0x00,0x00,
    // 53 '5'
    0x00,0x00,0xFE,0xC0,0xC0,0xC0,0xFC,0x06,0x06,0x06,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 54 '6'
    0x00,0x00,0x38,0x60,0xC0,0xC0,0xFC,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 55 '7'
    0x00,0x00,0xFE,0xC6,0x06,0x06,0x0C,0x18,0x30,0x30,0x30,0x30,0x00,0x00,0x00,0x00,
    // 56 '8'
    0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7C,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 57 '9'
    0x00,0x00,0x7C,0xC6,0xC6,0xC6,0x7E,0x06,0x06,0x06,0x0C,0x78,0x00,0x00,0x00,0x00,
    // 58 ':'
    0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x00,0x00,
    // 59 ';'
    0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00,0x18,0x18,0x30,0x00,0x00,0x00,0x00,
    // 60 '<'
    0x00,0x00,0x00,0x06,0x0C,0x18,0x30,0x60,0x30,0x18,0x0C,0x06,0x00,0x00,0x00,0x00,
    // 61 '='
    0x00,0x00,0x00,0x00,0x00,0x7E,0x00,0x00,0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 62 '>'
    0x00,0x00,0x00,0x60,0x30,0x18,0x0C,0x06,0x0C,0x18,0x30,0x60,0x00,0x00,0x00,0x00,
    // 63 '?'
    0x00,0x00,0x7C,0xC6,0xC6,0x0C,0x18,0x18,0x18,0x00,0x18,0x18,0x00,0x00,0x00,0x00,
    // 64 '@'
    0x00,0x00,0x7C,0xC6,0xC6,0xDE,0xDE,0xDE,0xDC,0xC0,0xC0,0x7C,0x00,0x00,0x00,0x00,
    // 65 'A'
    0x00,0x00,0x10,0x38,0x6C,0xC6,0xC6,0xFE,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00,
    // 66 'B'
    0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x66,0x66,0x66,0x66,0xFC,0x00,0x00,0x00,0x00,
    // 67 'C'
    0x00,0x00,0x3C,0x66,0xC2,0xC0,0xC0,0xC0,0xC0,0xC2,0x66,0x3C,0x00,0x00,0x00,0x00,
    // 68 'D'
    0x00,0x00,0xF8,0x6C,0x66,0x66,0x66,0x66,0x66,0x66,0x6C,0xF8,0x00,0x00,0x00,0x00,
    // 69 'E'
    0x00,0x00,0xFE,0x66,0x62,0x68,0x78,0x68,0x60,0x62,0x66,0xFE,0x00,0x00,0x00,0x00,
    // 70 'F'
    0x00,0x00,0xFE,0x66,0x62,0x68,0x78,0x68,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00,
    // 71 'G'
    0x00,0x00,0x3C,0x66,0xC2,0xC0,0xC0,0xDE,0xC6,0xC6,0x66,0x3A,0x00,0x00,0x00,0x00,
    // 72 'H'
    0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xFE,0xC6,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00,
    // 73 'I'
    0x00,0x00,0x3C,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00,
    // 74 'J'
    0x00,0x00,0x1E,0x0C,0x0C,0x0C,0x0C,0x0C,0xCC,0xCC,0xCC,0x78,0x00,0x00,0x00,0x00,
    // 75 'K'
    0x00,0x00,0xE6,0x66,0x66,0x6C,0x78,0x78,0x6C,0x66,0x66,0xE6,0x00,0x00,0x00,0x00,
    // 76 'L'
    0x00,0x00,0xF0,0x60,0x60,0x60,0x60,0x60,0x60,0x62,0x66,0xFE,0x00,0x00,0x00,0x00,
    // 77 'M'
    0x00,0x00,0xC6,0xEE,0xFE,0xFE,0xD6,0xC6,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00,
    // 78 'N'
    0x00,0x00,0xC6,0xE6,0xF6,0xFE,0xDE,0xCE,0xC6,0xC6,0xC6,0xC6,0x00,0x00,0x00,0x00,
    // 79 'O'
    0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 80 'P'
    0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x60,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00,
    // 81 'Q'
    0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xD6,0xDE,0x7C,0x0C,0x0E,0x00,0x00,
    // 82 'R'
    0x00,0x00,0xFC,0x66,0x66,0x66,0x7C,0x6C,0x66,0x66,0x66,0xE6,0x00,0x00,0x00,0x00,
    // 83 'S'
    0x00,0x00,0x7C,0xC6,0xC6,0x60,0x38,0x0C,0x06,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 84 'T'
    0x00,0x00,0xFF,0xDB,0x99,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00,
    // 85 'U'
    0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 86 'V'
    0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x6C,0x38,0x10,0x00,0x00,0x00,0x00,
    // 87 'W'
    0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xD6,0xD6,0xD6,0xFE,0xEE,0x6C,0x00,0x00,0x00,0x00,
    // 88 'X'
    0x00,0x00,0xC6,0xC6,0x6C,0x7C,0x38,0x38,0x7C,0x6C,0xC6,0xC6,0x00,0x00,0x00,0x00,
    // 89 'Y'
    0x00,0x00,0xC6,0xC6,0xC6,0x6C,0x38,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00,
    // 90 'Z'
    0x00,0x00,0xFE,0xC6,0x86,0x0C,0x18,0x30,0x60,0xC2,0xC6,0xFE,0x00,0x00,0x00,0x00,
    // 91 '['
    0x00,0x00,0x3C,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x30,0x3C,0x00,0x00,0x00,0x00,
    // 92 '\\'
    0x00,0x00,0x00,0x80,0xC0,0xE0,0x70,0x38,0x1C,0x0E,0x06,0x02,0x00,0x00,0x00,0x00,
    // 93 ']'
    0x00,0x00,0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00,0x00,0x00,0x00,
    // 94 '^'
    0x10,0x38,0x6C,0xC6,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 95 '_'
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0x00,0x00,
    // 96 '`'
    0x30,0x30,0x18,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    // 97 'a'
    0x00,0x00,0x00,0x00,0x00,0x78,0x0C,0x7C,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00,
    // 98 'b'
    0x00,0x00,0xE0,0x60,0x60,0x78,0x6C,0x66,0x66,0x66,0x66,0x7C,0x00,0x00,0x00,0x00,
    // 99 'c'
    0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC0,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 100 'd'
    0x00,0x00,0x1C,0x0C,0x0C,0x3C,0x6C,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00,
    // 101 'e'
    0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xFE,0xC0,0xC0,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 102 'f'
    0x00,0x00,0x1C,0x36,0x32,0x30,0x78,0x30,0x30,0x30,0x30,0x78,0x00,0x00,0x00,0x00,
    // 103 'g'
    0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0xCC,0xCC,0x7C,0x0C,0xCC,0x78,0x00,
    // 104 'h'
    0x00,0x00,0xE0,0x60,0x60,0x6C,0x76,0x66,0x66,0x66,0x66,0xE6,0x00,0x00,0x00,0x00,
    // 105 'i'
    0x00,0x00,0x18,0x18,0x00,0x38,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00,
    // 106 'j'
    0x00,0x00,0x06,0x06,0x00,0x0E,0x06,0x06,0x06,0x06,0x06,0x06,0x66,0x66,0x3C,0x00,
    // 107 'k'
    0x00,0x00,0xE0,0x60,0x60,0x66,0x6C,0x78,0x78,0x6C,0x66,0xE6,0x00,0x00,0x00,0x00,
    // 108 'l'
    0x00,0x00,0x38,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x00,0x00,0x00,0x00,
    // 109 'm'
    0x00,0x00,0x00,0x00,0x00,0xEC,0xFE,0xD6,0xD6,0xD6,0xD6,0xC6,0x00,0x00,0x00,0x00,
    // 110 'n'
    0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x66,0x66,0x00,0x00,0x00,0x00,
    // 111 'o'
    0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0xC6,0xC6,0xC6,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 112 'p'
    0x00,0x00,0x00,0x00,0x00,0xDC,0x66,0x66,0x66,0x66,0x66,0x7C,0x60,0x60,0xF0,0x00,
    // 113 'q'
    0x00,0x00,0x00,0x00,0x00,0x76,0xCC,0xCC,0xCC,0xCC,0xCC,0x7C,0x0C,0x0C,0x1E,0x00,
    // 114 'r'
    0x00,0x00,0x00,0x00,0x00,0xDC,0x76,0x66,0x60,0x60,0x60,0xF0,0x00,0x00,0x00,0x00,
    // 115 's'
    0x00,0x00,0x00,0x00,0x00,0x7C,0xC6,0x60,0x38,0x0C,0xC6,0x7C,0x00,0x00,0x00,0x00,
    // 116 't'
    0x00,0x00,0x10,0x30,0x30,0xFC,0x30,0x30,0x30,0x30,0x36,0x1C,0x00,0x00,0x00,0x00,
    // 117 'u'
    0x00,0x00,0x00,0x00,0x00,0xCC,0xCC,0xCC,0xCC,0xCC,0xCC,0x76,0x00,0x00,0x00,0x00,
    // 118 'v'
    0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0x6C,0x38,0x00,0x00,0x00,0x00,
    // 119 'w'
    0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xD6,0xD6,0xD6,0xFE,0x6C,0x00,0x00,0x00,0x00,
    // 120 'x'
    0x00,0x00,0x00,0x00,0x00,0xC6,0x6C,0x38,0x38,0x38,0x6C,0xC6,0x00,0x00,0x00,0x00,
    // 121 'y'
    0x00,0x00,0x00,0x00,0x00,0xC6,0xC6,0xC6,0xC6,0xC6,0xC6,0x7E,0x06,0x0C,0xF8,0x00,
    // 122 'z'
    0x00,0x00,0x00,0x00,0x00,0xFE,0xCC,0x18,0x30,0x60,0xC6,0xFE,0x00,0x00,0x00,0x00,
    // 123 '{'
    0x00,0x00,0x0E,0x18,0x18,0x18,0x70,0x18,0x18,0x18,0x18,0x0E,0x00,0x00,0x00,0x00,
    // 124 '|'
    0x00,0x00,0x18,0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x18,0x18,0x00,0x00,0x00,0x00,
    // 125 '}'
    0x00,0x00,0x70,0x18,0x18,0x18,0x0E,0x18,0x18,0x18,0x18,0x70,0x00,0x00,0x00,0x00,
    // 126 '~'
    0x00,0x00,0x76,0xDC,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
];

/// Draw text on the image using the embedded 8×16 bitmap font.
///
/// * `size` — 1 for 8×16, 2 for 16×32 (2× scaled)
/// * `anchor` — `"left"`, `"center"`, or `"right"` horizontal alignment relative to (x, y)
pub fn draw_text(
    handle: &mut ImageHandle,
    x: i32,
    y: i32,
    text: &str,
    size: u8,
    color: [u8; 4],
    anchor: &str,
) {
    let scale = (size as i32).max(1);
    let glyph_w = 8 * scale;
    let glyph_h = 16 * scale;
    let text_width = text.len() as i32 * glyph_w;

    // Compute starting x based on anchor
    let start_x = match anchor {
        "center" => x - text_width / 2,
        "right" => x - text_width,
        _ => x, // "left" or default
    };

    let (w, h) = handle.inner.dimensions();
    let pixel = color_to_pixel(handle, color);

    for (ci, ch) in text.chars().enumerate() {
        let code = ch as u32;
        if !(32..=126).contains(&code) {
            continue; // skip non-printable
        }
        let glyph_idx = (code - 32) as usize;
        let glyph_offset = glyph_idx * 16;
        let char_x = start_x + (ci as i32) * glyph_w;

        for row in 0..16 {
            let bits = FONT_8X16[glyph_offset + row];
            for col in 0..8 {
                if bits & (0x80 >> col) != 0 {
                    // Draw scaled pixel
                    for sy in 0..scale {
                        for sx in 0..scale {
                            let px = char_x + col * scale + sx;
                            let py = y + (row as i32) * scale + sy;
                            if px >= 0 && px < w as i32 && py >= 0 && py < h as i32 {
                                handle.inner.put_pixel(px as u32, py as u32, pixel);
                            }
                        }
                    }
                }
            }
        }
    }

    let _ = glyph_h; // suppress unused warning
}

// ---------------------------------------------------------------------------
// TrueType font support (via ab_glyph)
// ---------------------------------------------------------------------------

/// Embedded default font (Liberation Sans Regular).
static DEFAULT_FONT_DATA: &[u8] = include_bytes!("fonts/LiberationSans-Regular.ttf");

/// A loaded TrueType font at a specific pixel size.
pub struct FontHandle {
    pub font: FontArc,
    pub px_size: f32,
}

impl Clone for FontHandle {
    fn clone(&self) -> Self {
        Self {
            font: self.font.clone(),
            px_size: self.px_size,
        }
    }
}

/// Load a TrueType font from raw TTF/OTF data at the given pixel size.
pub fn font_load(data: &[u8], px_size: f32) -> Result<FontHandle> {
    let font = FontArc::try_from_vec(data.to_vec())
        .map_err(|_| PilError::InvalidOperation("invalid font data".into()))?;
    Ok(FontHandle { font, px_size })
}

/// Load the embedded default font at the given pixel size.
pub fn font_load_default(px_size: f32) -> FontHandle {
    let font = FontArc::try_from_slice(DEFAULT_FONT_DATA).expect("embedded font data is valid");
    FontHandle { font, px_size }
}

/// Return (ascent, descent, line_height) for a font.
pub fn font_metrics(fh: &FontHandle) -> (f32, f32, f32) {
    let scale = PxScale::from(fh.px_size);
    let scaled = fh.font.as_scaled(scale);
    let ascent = scaled.ascent();
    let descent = scaled.descent(); // negative value
    let height = scaled.height();
    (ascent, -descent, height)
}

/// Return the pixel width of a single line of text.
pub fn font_text_length(fh: &FontHandle, text: &str) -> f32 {
    let scale = PxScale::from(fh.px_size);
    let scaled = fh.font.as_scaled(scale);
    let mut width = 0.0f32;
    let mut prev_glyph: Option<ab_glyph::GlyphId> = None;
    for ch in text.chars() {
        let glyph_id = scaled.glyph_id(ch);
        if let Some(prev) = prev_glyph {
            width += scaled.kern(prev, glyph_id);
        }
        width += scaled.h_advance(glyph_id);
        prev_glyph = Some(glyph_id);
    }
    width
}

/// Return bounding box (x0, y0, x1, y1) for text at position (x, y).
pub fn font_text_bbox(fh: &FontHandle, text: &str, x: f32, y: f32) -> (f32, f32, f32, f32) {
    let scale = PxScale::from(fh.px_size);
    let scaled = fh.font.as_scaled(scale);
    let ascent = scaled.ascent();
    let descent = scaled.descent();
    let width = font_text_length(fh, text);
    (x, y - ascent, x + width, y - descent)
}

/// Draw TrueType text onto an image.
pub fn draw_text_ttf(
    handle: &mut ImageHandle,
    fh: &FontHandle,
    x: f32,
    y: f32,
    text: &str,
    color: [u8; 4],
    anchor: &str,
) {
    let scale = PxScale::from(fh.px_size);
    let scaled = fh.font.as_scaled(scale);
    let ascent = scaled.ascent();

    // Compute text width for anchor alignment
    let text_width = font_text_length(fh, text);
    let start_x = match anchor {
        "center" | "mm" => x - text_width / 2.0,
        "right" | "rm" | "ra" => x - text_width,
        _ => x,
    };

    // Baseline y: "y" is the top of the text box in Pillow convention
    let baseline_y = y + ascent;

    let (img_w, img_h) = handle.inner.dimensions();
    let pixel = image::Rgba(color);

    let mut cursor_x = start_x;
    let mut prev_glyph: Option<ab_glyph::GlyphId> = None;

    for ch in text.chars() {
        let glyph_id = scaled.glyph_id(ch);
        if let Some(prev) = prev_glyph {
            cursor_x += scaled.kern(prev, glyph_id);
        }

        let glyph = glyph_id.with_scale_and_position(scale, ab_glyph::point(cursor_x, baseline_y));

        if let Some(outlined) = fh.font.outline_glyph(glyph) {
            let bounds = outlined.px_bounds();
            outlined.draw(|gx, gy, coverage| {
                let px = gx as i32 + bounds.min.x as i32;
                let py = gy as i32 + bounds.min.y as i32;
                if px >= 0 && px < img_w as i32 && py >= 0 && py < img_h as i32 {
                    if coverage >= 0.99 {
                        handle.inner.put_pixel(px as u32, py as u32, pixel);
                    } else if coverage > 0.01 {
                        // Alpha blend with existing pixel
                        let dst = handle.inner.get_pixel(px as u32, py as u32);
                        let a = coverage;
                        let blend = |s: u8, d: u8| -> u8 {
                            (s as f32 * a + d as f32 * (1.0 - a)).round() as u8
                        };
                        let blended = image::Rgba([
                            blend(color[0], dst.0[0]),
                            blend(color[1], dst.0[1]),
                            blend(color[2], dst.0[2]),
                            blend(color[3], dst.0[3]),
                        ]);
                        handle.inner.put_pixel(px as u32, py as u32, blended);
                    }
                }
            });
        }

        cursor_x += scaled.h_advance(glyph_id);
        prev_glyph = Some(glyph_id);
    }
}

// ---------------------------------------------------------------------------
// Paste (compositing)
// ---------------------------------------------------------------------------

pub fn paste(dst: &mut ImageHandle, src: &ImageHandle, x: i32, y: i32, mask: Option<&ImageHandle>) {
    let (dw, dh) = dst.inner.dimensions();
    let (sw, sh) = src.inner.dimensions();

    for sy in 0..sh {
        for sx in 0..sw {
            let dx = x + sx as i32;
            let dy = y + sy as i32;
            if dx < 0 || dy < 0 || dx >= dw as i32 || dy >= dh as i32 {
                continue;
            }
            let src_pixel = src.inner.get_pixel(sx, sy);
            let alpha = match &mask {
                Some(m) => {
                    let (mw, mh) = m.inner.dimensions();
                    if sx < mw && sy < mh {
                        m.inner.get_pixel(sx, sy).0[0] // use first channel as alpha
                    } else {
                        0
                    }
                }
                None => 255,
            };
            if alpha == 255 {
                putpixel(dst, dx as u32, dy as u32, src_pixel.0);
            } else if alpha > 0 {
                let dst_pixel = dst.inner.get_pixel(dx as u32, dy as u32);
                let a = alpha as f32 / 255.0;
                let blend =
                    |s: u8, d: u8| -> u8 { (s as f32 * a + d as f32 * (1.0 - a)).round() as u8 };
                let blended = [
                    blend(src_pixel.0[0], dst_pixel.0[0]),
                    blend(src_pixel.0[1], dst_pixel.0[1]),
                    blend(src_pixel.0[2], dst_pixel.0[2]),
                    blend(src_pixel.0[3], dst_pixel.0[3]),
                ];
                putpixel(dst, dx as u32, dy as u32, blended);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Channel operations
// ---------------------------------------------------------------------------

pub fn split(handle: &ImageHandle) -> Vec<ImageHandle> {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);

    // Determine number of bands and which RGBA indices to pull them from
    // to_rgba8() converts all formats: Rgb8→[R,G,B,255], LumaA8→[L,L,L,A], etc.
    let rgba = handle.inner.to_rgba8();

    let (num, indices): (usize, Vec<usize>) = match m {
        "L" | "P" | "1" => (1, vec![0]),
        "LA" | "La" | "PA" => (2, vec![0, 3]),
        "RGB" | "YCbCr" | "LAB" | "HSV" => (3, vec![0, 1, 2]),
        "RGBA" | "CMYK" | "RGBX" | "RGBa" => (4, vec![0, 1, 2, 3]),
        "I" | "F" | "I;16" | "I;16L" | "I;16B" | "I;16N" => (1, vec![0]),
        _ => (4, vec![0, 1, 2, 3]),
    };

    let _ = num;
    indices
        .into_iter()
        .map(|idx| {
            let buf = ImageBuffer::from_fn(w, h, |x, y| image::Luma([rgba.get_pixel(x, y).0[idx]]));
            ImageHandle {
                inner: DynamicImage::ImageLuma8(buf),
                mode_override: None,
                palette: None,
                palette_mode: None,
            }
        })
        .collect()
}

pub fn merge(target_mode: &str, channels: &[&ImageHandle]) -> Result<ImageHandle> {
    let (w, h) = if let Some(first) = channels.first() {
        first.inner.dimensions()
    } else {
        return Err(PilError::InvalidOperation("no channels provided".into()));
    };

    let get_ch =
        |ch_idx: usize, x: u32, y: u32| -> u8 { channels[ch_idx].inner.get_pixel(x, y).0[0] };

    let img = match target_mode {
        "L" => {
            if channels.is_empty() {
                return Err(PilError::InvalidOperation("L requires 1 channel".into()));
            }
            DynamicImage::ImageLuma8(ImageBuffer::from_fn(w, h, |x, y| {
                image::Luma([get_ch(0, x, y)])
            }))
        }
        "LA" => {
            if channels.len() < 2 {
                return Err(PilError::InvalidOperation("LA requires 2 channels".into()));
            }
            DynamicImage::ImageLumaA8(ImageBuffer::from_fn(w, h, |x, y| {
                image::LumaA([get_ch(0, x, y), get_ch(1, x, y)])
            }))
        }
        "RGB" => {
            if channels.len() < 3 {
                return Err(PilError::InvalidOperation("RGB requires 3 channels".into()));
            }
            DynamicImage::ImageRgb8(ImageBuffer::from_fn(w, h, |x, y| {
                image::Rgb([get_ch(0, x, y), get_ch(1, x, y), get_ch(2, x, y)])
            }))
        }
        "RGBA" => {
            if channels.len() < 4 {
                return Err(PilError::InvalidOperation(
                    "RGBA requires 4 channels".into(),
                ));
            }
            DynamicImage::ImageRgba8(ImageBuffer::from_fn(w, h, |x, y| {
                image::Rgba([
                    get_ch(0, x, y),
                    get_ch(1, x, y),
                    get_ch(2, x, y),
                    get_ch(3, x, y),
                ])
            }))
        }
        "PA" => {
            // P channel (indices) + A channel — merge into LumaA8 with P palette from ch0
            if channels.len() < 2 {
                return Err(PilError::InvalidOperation("PA requires 2 channels".into()));
            }
            let buf = ImageBuffer::from_fn(w, h, |x, y| {
                image::LumaA([get_ch(0, x, y), get_ch(1, x, y)])
            });
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(buf),
                mode_override: Some("PA"),
                palette: channels[0].palette.clone(),
                palette_mode: channels[0].palette_mode.clone(),
            });
        }
        _ => return Err(PilError::UnsupportedMode(target_mode.to_string())),
    };
    Ok(ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

/// Extract band n (0-based) as an L-mode image.
pub fn getband(handle: &ImageHandle, n: usize) -> Result<ImageHandle> {
    let bands = split(handle);
    bands
        .into_iter()
        .nth(n)
        .map(Ok)
        .unwrap_or_else(|| Err(PilError::InvalidOperation(format!("band {n} out of range"))))
}

/// Replace band n with src (L-mode, same size).
pub fn putband(handle: &ImageHandle, src: &ImageHandle, n: usize) -> Result<ImageHandle> {
    let mut bands = split(handle);
    if n >= bands.len() {
        return Err(PilError::InvalidOperation(format!("band {n} out of range")));
    }
    bands[n] = src.clone();
    let refs: Vec<&ImageHandle> = bands.iter().collect();
    merge(mode(handle), &refs)
}

/// Fill band n with constant value.
pub fn fillband(handle: &ImageHandle, n: usize, value: u8) -> Result<ImageHandle> {
    let (w, h) = (handle.inner.width(), handle.inner.height());
    let flat = new_image("L", w, h, &[value])?;
    putband(handle, &flat, n)
}

// ---------------------------------------------------------------------------
// Statistics / analysis
// ---------------------------------------------------------------------------

pub fn histogram(handle: &ImageHandle) -> Vec<u32> {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    // Mode "1" returns 2-bucket histogram (0=black, 1=white)
    if m == "1" {
        let mut hist = vec![0u32; 2];
        let luma = handle.inner.to_luma8();
        for y in 0..h {
            for x in 0..w {
                let v = luma.get_pixel(x, y)[0];
                if v >= 128 {
                    hist[1] += 1;
                } else {
                    hist[0] += 1;
                }
            }
        }
        return hist;
    }
    // P mode: count palette indices directly from the Luma8 buffer
    if m == "P" || m == "PA" {
        let mut hist = vec![0u32; 256];
        if let image::DynamicImage::ImageLuma8(luma) = &handle.inner {
            for px in luma.pixels() {
                hist[px[0] as usize] += 1;
            }
        }
        return hist;
    }
    let num_channels = match m {
        "L" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };
    let mut hist = vec![0u32; 256 * num_channels];
    let rgba = handle.inner.to_rgba8();
    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y).0;
            match m {
                "L" => {
                    hist[p[0] as usize] += 1;
                }
                "LA" => {
                    hist[p[0] as usize] += 1;
                    hist[256 + p[3] as usize] += 1;
                }
                "RGB" => {
                    hist[p[0] as usize] += 1;
                    hist[256 + p[1] as usize] += 1;
                    hist[512 + p[2] as usize] += 1;
                }
                _ => {
                    hist[p[0] as usize] += 1;
                    hist[256 + p[1] as usize] += 1;
                    hist[512 + p[2] as usize] += 1;
                    hist[768 + p[3] as usize] += 1;
                }
            }
        }
    }
    hist
}

pub fn getbbox(handle: &ImageHandle) -> Option<(u32, u32, u32, u32)> {
    let (w, h) = handle.inner.dimensions();
    let mut min_x = w;
    let mut min_y = h;
    let mut max_x = 0u32;
    let mut max_y = 0u32;

    let check_alpha = matches!(
        &handle.inner,
        DynamicImage::ImageRgba8(_) | DynamicImage::ImageLumaA8(_)
    );
    for y in 0..h {
        for x in 0..w {
            let p = handle.inner.get_pixel(x, y).0;
            let nonzero = p[0] != 0 || p[1] != 0 || p[2] != 0 || (check_alpha && p[3] != 0);
            if nonzero {
                min_x = min_x.min(x);
                min_y = min_y.min(y);
                max_x = max_x.max(x);
                max_y = max_y.max(y);
            }
        }
    }
    if max_x < min_x {
        None
    } else {
        Some((min_x, min_y, max_x + 1, max_y + 1))
    }
}

pub fn getextrema(handle: &ImageHandle) -> Vec<(u8, u8)> {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let num_channels = match m {
        "L" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };
    let mut mins = vec![255u8; num_channels];
    let mut maxs = vec![0u8; num_channels];
    let rgba = handle.inner.to_rgba8();

    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y).0;
            let channels: Vec<u8> = match m {
                "L" => vec![p[0]],
                "LA" => vec![p[0], p[3]],
                "RGB" => vec![p[0], p[1], p[2]],
                _ => vec![p[0], p[1], p[2], p[3]],
            };
            for (i, &v) in channels.iter().enumerate() {
                if v < mins[i] {
                    mins[i] = v;
                }
                if v > maxs[i] {
                    maxs[i] = v;
                }
            }
        }
    }
    mins.into_iter().zip(maxs).collect()
}

// ---------------------------------------------------------------------------
// Construct from raw bytes
// ---------------------------------------------------------------------------

pub fn frombytes(mode_str: &str, width: u32, height: u32, data: &[u8]) -> Result<ImageHandle> {
    let img = match mode_str {
        "L" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            DynamicImage::ImageLuma8(buf)
        }
        "LA" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            DynamicImage::ImageLumaA8(buf)
        }
        "RGB" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            DynamicImage::ImageRgb8(buf)
        }
        "RGBA" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            DynamicImage::ImageRgba8(buf)
        }
        "1" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(buf),
                mode_override: Some("1"),
                palette: None,
                palette_mode: None,
            });
        }
        "I" | "F" | "I;16" | "I;16L" | "I;16N" => {
            // Stored as Luma16 (2 bytes per pixel, little-endian)
            let buf: ImageBuffer<Luma<u16>, Vec<u16>> = {
                let shorts: Vec<u16> = data
                    .chunks_exact(2)
                    .map(|c| u16::from_le_bytes([c[0], c[1]]))
                    .collect();
                ImageBuffer::from_raw(width, height, shorts)
                    .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?
            };
            let mo: Option<&'static str> = match mode_str {
                "I" => Some("I"),
                "F" => Some("F"),
                "I;16" => Some("I;16"),
                "I;16L" => Some("I;16L"),
                "I;16N" => Some("I;16N"),
                _ => None,
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma16(buf),
                mode_override: mo,
                palette: None,
                palette_mode: None,
            });
        }
        "I;16B" => {
            // Big-endian 16-bit: parse BE bytes, store as LE u16 internally
            let buf: ImageBuffer<Luma<u16>, Vec<u16>> = {
                let shorts: Vec<u16> = data
                    .chunks_exact(2)
                    .map(|c| u16::from_be_bytes([c[0], c[1]]))
                    .collect();
                ImageBuffer::from_raw(width, height, shorts)
                    .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma16(buf),
                mode_override: Some("I;16B"),
                palette: None,
                palette_mode: None,
            });
        }
        "P" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(buf),
                mode_override: Some("P"),
                palette: None,
                palette_mode: None,
            });
        }
        "PA" => {
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            return Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(buf),
                mode_override: Some("PA"),
                palette: None,
                palette_mode: None,
            });
        }
        "CMYK" | "RGBX" | "RGBa" => {
            // 4-channel modes stored as Rgba8
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            let mo: Option<&'static str> = match mode_str {
                "CMYK" => Some("CMYK"),
                "RGBX" => Some("RGBX"),
                "RGBa" => Some("RGBa"),
                _ => None,
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(buf),
                mode_override: mo,
                palette: None,
                palette_mode: None,
            });
        }
        "YCbCr" | "LAB" | "HSV" => {
            // 3-channel color-space modes stored as Rgb8
            let buf = ImageBuffer::from_raw(width, height, data.to_vec())
                .ok_or_else(|| PilError::InvalidOperation("buffer size mismatch".into()))?;
            let mo: Option<&'static str> = match mode_str {
                "YCbCr" => Some("YCbCr"),
                "LAB" => Some("LAB"),
                "HSV" => Some("HSV"),
                _ => None,
            };
            return Ok(ImageHandle {
                inner: DynamicImage::ImageRgb8(buf),
                mode_override: mo,
                palette: None,
                palette_mode: None,
            });
        }
        _ => return Err(PilError::UnsupportedMode(mode_str.to_string())),
    };
    Ok(ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

// ---------------------------------------------------------------------------
// Image enhancement
// ---------------------------------------------------------------------------

pub fn adjust_brightness(handle: &ImageHandle, factor: f32) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let rgba = handle.inner.to_rgba8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        let clamp = |v: f32| -> u8 { v.round().clamp(0.0, 255.0) as u8 };
        image::Rgba([
            clamp(p[0] as f32 * factor),
            clamp(p[1] as f32 * factor),
            clamp(p[2] as f32 * factor),
            p[3],
        ])
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::ImageRgba8(out.clone()).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::ImageRgba8(out.clone()).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn adjust_contrast(handle: &ImageHandle, factor: f32) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    // Compute mean luminance
    let gray = handle.inner.to_luma8();
    let mut sum = 0u64;
    for p in gray.pixels() {
        sum += p.0[0] as u64;
    }
    let mean = sum as f32 / (w * h) as f32;

    let rgba = handle.inner.to_rgba8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        let clamp = |v: f32| -> u8 { v.round().clamp(0.0, 255.0) as u8 };
        image::Rgba([
            clamp(mean + (p[0] as f32 - mean) * factor),
            clamp(mean + (p[1] as f32 - mean) * factor),
            clamp(mean + (p[2] as f32 - mean) * factor),
            p[3],
        ])
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::from(out).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::from(out).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn adjust_color(handle: &ImageHandle, factor: f32) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let rgba = handle.inner.to_rgba8();
    let gray = handle.inner.to_luma8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        let g = gray.get_pixel(x, y).0[0];
        let clamp = |v: f32| -> u8 { v.round().clamp(0.0, 255.0) as u8 };
        // Blend between grayscale (factor=0) and original (factor=1)
        image::Rgba([
            clamp(g as f32 + (p[0] as f32 - g as f32) * factor),
            clamp(g as f32 + (p[1] as f32 - g as f32) * factor),
            clamp(g as f32 + (p[2] as f32 - g as f32) * factor),
            p[3],
        ])
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::from(out).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::from(out).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn adjust_sharpness(handle: &ImageHandle, factor: f32) -> ImageHandle {
    // Blend between blurred (factor=0) and original (factor=1), with >1 sharpening
    let blurred = handle.inner.blur(1.0);
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let orig = handle.inner.to_rgba8();
    let blur = blurred.to_rgba8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let o = orig.get_pixel(x, y).0;
        let b = blur.get_pixel(x, y).0;
        let clamp = |v: f32| -> u8 { v.round().clamp(0.0, 255.0) as u8 };
        image::Rgba([
            clamp(b[0] as f32 + (o[0] as f32 - b[0] as f32) * factor),
            clamp(b[1] as f32 + (o[1] as f32 - b[1] as f32) * factor),
            clamp(b[2] as f32 + (o[2] as f32 - b[2] as f32) * factor),
            o[3],
        ])
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::from(out).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::from(out).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

// ---------------------------------------------------------------------------
// ImageOps
// ---------------------------------------------------------------------------

pub fn autocontrast(handle: &ImageHandle) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let hist = histogram(handle);
    let num_ch = match m {
        "L" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };

    // Find min/max for each channel (skip alpha for stretching)
    let stretch_ch = match m {
        "LA" => 1,
        "RGBA" => 3,
        _ => num_ch,
    };
    let mut ch_min = vec![0u8; num_ch];
    let mut ch_max = vec![255u8; num_ch];
    for c in 0..stretch_ch {
        for i in 0..256 {
            if hist[c * 256 + i] > 0 {
                ch_min[c] = i as u8;
                break;
            }
        }
        for i in (0..256).rev() {
            if hist[c * 256 + i] > 0 {
                ch_max[c] = i as u8;
                break;
            }
        }
    }

    let rgba = handle.inner.to_rgba8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        let stretch = |v: u8, lo: u8, hi: u8| -> u8 {
            if hi <= lo {
                return v;
            }
            ((v.max(lo) - lo) as f32 / (hi - lo) as f32 * 255.0)
                .round()
                .min(255.0) as u8
        };
        match m {
            "L" => {
                let v = stretch(p[0], ch_min[0], ch_max[0]);
                image::Rgba([v, v, v, p[3]])
            }
            "RGB" => image::Rgba([
                stretch(p[0], ch_min[0], ch_max[0]),
                stretch(p[1], ch_min[1], ch_max[1]),
                stretch(p[2], ch_min[2], ch_max[2]),
                p[3],
            ]),
            _ => image::Rgba([
                stretch(p[0], ch_min[0], ch_max[0]),
                stretch(p[1], ch_min[1], ch_max[1]),
                stretch(p[2], ch_min[2], ch_max[2]),
                p[3],
            ]),
        }
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::from(out).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::from(out).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn invert_image(handle: &ImageHandle) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let rgba = handle.inner.to_rgba8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        image::Rgba([255 - p[0], 255 - p[1], 255 - p[2], p[3]])
    });
    let img = match m {
        "L" => DynamicImage::ImageLuma8(DynamicImage::from(out).to_luma8()),
        "RGB" => DynamicImage::ImageRgb8(DynamicImage::from(out).to_rgb8()),
        _ => DynamicImage::ImageRgba8(out),
    };
    ImageHandle {
        inner: img,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn parse_rgb(color: &[u8]) -> (u8, u8, u8) {
    let r = color.first().copied().unwrap_or(0);
    let g = color.get(1).copied().unwrap_or(0);
    let b = color.get(2).copied().unwrap_or(0);
    (r, g, b)
}

fn parse_rgba(color: &[u8]) -> (u8, u8, u8, u8) {
    let r = color.first().copied().unwrap_or(0);
    let g = color.get(1).copied().unwrap_or(0);
    let b = color.get(2).copied().unwrap_or(0);
    let a = color.get(3).copied().unwrap_or(255);
    (r, g, b, a)
}

fn parse_format(format: &str) -> Result<ImageFormat> {
    match format.to_ascii_lowercase().as_str() {
        "png" => Ok(ImageFormat::Png),
        "jpeg" | "jpg" => Ok(ImageFormat::Jpeg),
        "gif" => Ok(ImageFormat::Gif),
        "bmp" => Ok(ImageFormat::Bmp),
        "tiff" | "tif" => Ok(ImageFormat::Tiff),
        "webp" => Ok(ImageFormat::WebP),
        _ => Err(PilError::UnsupportedFormat(format.to_string())),
    }
}

// ---------------------------------------------------------------------------
// putdata — set all pixels from a flat byte slice
// ---------------------------------------------------------------------------

pub fn putdata(handle: &mut ImageHandle, data: &[u8]) {
    // Mode "1": normalize any non-zero value to 255 (Pillow stores 0 or 255 internally)
    if matches!(handle.mode_override, Some(m) if m == "1") {
        let normalized: Vec<u8> = data.iter().map(|&v| if v != 0 { 255 } else { 0 }).collect();
        let (w, h) = handle.inner.dimensions();
        let mut idx = 0usize;
        for y in 0..h {
            for x in 0..w {
                if idx >= normalized.len() {
                    return;
                }
                putpixel(
                    handle,
                    x,
                    y,
                    [normalized[idx], normalized[idx], normalized[idx], 255],
                );
                idx += 1;
            }
        }
        return;
    }
    let (w, h) = handle.inner.dimensions();
    let bands = match &handle.inner {
        DynamicImage::ImageLuma8(_) => 1,
        DynamicImage::ImageLumaA8(_) => 2,
        DynamicImage::ImageRgb8(_) => 3,
        DynamicImage::ImageRgba8(_) => 4,
        _ => 1,
    };
    let mut idx = 0usize;
    for y in 0..h {
        for x in 0..w {
            if idx + bands > data.len() {
                return;
            }
            let color = match bands {
                1 => [data[idx], data[idx], data[idx], 255],
                2 => [data[idx], data[idx + 1], 0, 255],
                3 => [data[idx], data[idx + 1], data[idx + 2], 255],
                4 => [data[idx], data[idx + 1], data[idx + 2], data[idx + 3]],
                _ => [0, 0, 0, 255],
            };
            putpixel(handle, x, y, color);
            idx += bands;
        }
    }
}

/// Write 16-bit pixel data (2 LE bytes per pixel) into a Luma16 image.
pub fn putdata_16bit(handle: &mut ImageHandle, data: &[u8]) {
    if let DynamicImage::ImageLuma16(buf) = &mut handle.inner {
        let (w, h) = buf.dimensions();
        let mut idx = 0usize;
        for y in 0..h {
            for x in 0..w {
                if idx + 2 > data.len() {
                    return;
                }
                let v = u16::from_le_bytes([data[idx], data[idx + 1]]);
                buf.put_pixel(x, y, Luma([v]));
                idx += 2;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// point — apply a lookup table or function to each pixel
// ---------------------------------------------------------------------------

pub fn point(handle: &ImageHandle, lut: &[u8]) -> Result<ImageHandle> {
    let (w, h) = handle.inner.dimensions();
    match &handle.inner {
        DynamicImage::ImageLuma8(buf) => {
            if lut.len() < 256 {
                return Err(PilError::InvalidOperation("LUT too short".into()));
            }
            let mut out = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(x, y, image::Luma([lut[px[0] as usize]]));
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
        DynamicImage::ImageLumaA8(buf) => {
            if lut.len() < 512 {
                return Err(PilError::InvalidOperation("LUT too short for LA".into()));
            }
            let mut out: ImageBuffer<image::LumaA<u8>, Vec<u8>> = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(
                    x,
                    y,
                    image::LumaA([lut[px[0] as usize], lut[256 + px[1] as usize]]),
                );
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageLumaA8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
        DynamicImage::ImageRgb8(buf) => {
            // Accept either 768-element (per-channel) or 256-element (broadcast) LUTs
            if lut.len() < 256 {
                return Err(PilError::InvalidOperation("LUT too short for RGB".into()));
            }
            let (r_lut, g_lut, b_lut) = if lut.len() >= 768 {
                (&lut[0..256], &lut[256..512], &lut[512..768])
            } else {
                (&lut[0..256], &lut[0..256], &lut[0..256])
            };
            let mut out = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(
                    x,
                    y,
                    image::Rgb([
                        r_lut[px[0] as usize],
                        g_lut[px[1] as usize],
                        b_lut[px[2] as usize],
                    ]),
                );
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgb8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
        DynamicImage::ImageRgba8(buf) => {
            // Accept 1024, 768 (no alpha lut), or 256 (broadcast) element LUTs
            if lut.len() < 256 {
                return Err(PilError::InvalidOperation("LUT too short for RGBA".into()));
            }
            let (r_lut, g_lut, b_lut, a_lut) = if lut.len() >= 1024 {
                (
                    &lut[0..256],
                    &lut[256..512],
                    &lut[512..768],
                    &lut[768..1024],
                )
            } else if lut.len() >= 768 {
                (&lut[0..256], &lut[256..512], &lut[512..768], &lut[0..256])
            } else {
                (&lut[0..256], &lut[0..256], &lut[0..256], &lut[0..256])
            };
            let mut out = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(
                    x,
                    y,
                    image::Rgba([
                        r_lut[px[0] as usize],
                        g_lut[px[1] as usize],
                        b_lut[px[2] as usize],
                        a_lut[px[3] as usize],
                    ]),
                );
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(out),
                mode_override: handle.mode_override,
                palette: None,
                palette_mode: None,
            })
        }
        _ => Err(PilError::InvalidOperation(
            "point() not supported for this mode".into(),
        )),
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn parse_filter(filter: &str) -> image::imageops::FilterType {
    match filter.to_ascii_lowercase().as_str() {
        "nearest" | "0" => image::imageops::FilterType::Nearest,
        "bilinear" | "linear" | "2" => image::imageops::FilterType::Triangle,
        "bicubic" | "cubic" | "3" => image::imageops::FilterType::CatmullRom,
        "lanczos" | "1" => image::imageops::FilterType::Lanczos3,
        _ => image::imageops::FilterType::Triangle,
    }
}

// ---------------------------------------------------------------------------
// Blend / Composite
// ---------------------------------------------------------------------------

/// Linear interpolation: out = im1 * (1 - alpha) + im2 * alpha
pub fn blend(im1: &ImageHandle, im2: &ImageHandle, alpha: f64) -> Result<ImageHandle> {
    let src_mode = mode(im1);
    let a = im1.inner.to_rgba8();
    let b = im2.inner.to_rgba8();
    let (w, h) = a.dimensions();
    if b.dimensions() != (w, h) {
        return Err(PilError::InvalidOperation(
            "images must be same size".into(),
        ));
    }
    let inv = 1.0 - alpha;
    // Preserve the mode of the input images
    match src_mode {
        "L" => {
            let mut out = image::GrayImage::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    let pa = a.get_pixel(x, y);
                    let pb = b.get_pixel(x, y);
                    let v = (pa[0] as f64 * inv + pb[0] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    out.put_pixel(x, y, image::Luma([v]));
                }
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageLuma8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
        "RGB" => {
            let mut out = image::RgbImage::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    let pa = a.get_pixel(x, y);
                    let pb = b.get_pixel(x, y);
                    let r = (pa[0] as f64 * inv + pb[0] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    let g = (pa[1] as f64 * inv + pb[1] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    let bl = (pa[2] as f64 * inv + pb[2] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    out.put_pixel(x, y, image::Rgb([r, g, bl]));
                }
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgb8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
        _ => {
            // Default: RGBA
            let mut out = image::RgbaImage::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    let pa = a.get_pixel(x, y);
                    let pb = b.get_pixel(x, y);
                    let r = (pa[0] as f64 * inv + pb[0] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    let g = (pa[1] as f64 * inv + pb[1] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    let bl = (pa[2] as f64 * inv + pb[2] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    let al = (pa[3] as f64 * inv + pb[3] as f64 * alpha).clamp(0.0, 255.0) as u8;
                    out.put_pixel(x, y, image::Rgba([r, g, bl, al]));
                }
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(out),
                mode_override: None,
                palette: None,
                palette_mode: None,
            })
        }
    }
}

/// Composite two images using a mask: out = im1 where mask=0, im2 where mask=255
pub fn composite(im1: &ImageHandle, im2: &ImageHandle, mask: &ImageHandle) -> Result<ImageHandle> {
    let a = im1.inner.to_rgba8();
    let b = im2.inner.to_rgba8();
    let m = mask.inner.to_luma8();
    let (w, h) = a.dimensions();
    if b.dimensions() != (w, h) || m.dimensions() != (w, h) {
        return Err(PilError::InvalidOperation(
            "images must be same size".into(),
        ));
    }
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let pa = a.get_pixel(x, y);
            let pb = b.get_pixel(x, y);
            let mv = m.get_pixel(x, y)[0] as f64 / 255.0;
            let inv = 1.0 - mv;
            // Pillow: mask=255 → im1, mask=0 → im2
            let r = (pa[0] as f64 * mv + pb[0] as f64 * inv) as u8;
            let g = (pa[1] as f64 * mv + pb[1] as f64 * inv) as u8;
            let bl = (pa[2] as f64 * mv + pb[2] as f64 * inv) as u8;
            let al = (pa[3] as f64 * mv + pb[3] as f64 * inv) as u8;
            out.put_pixel(x, y, image::Rgba([r, g, bl, al]));
        }
    }
    Ok(ImageHandle {
        inner: DynamicImage::ImageRgba8(out),
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

/// Alpha composite: place src over dst using src alpha
pub fn alpha_composite(dst: &ImageHandle, src: &ImageHandle) -> Result<ImageHandle> {
    let a = dst.inner.to_rgba8();
    let b = src.inner.to_rgba8();
    let (w, h) = a.dimensions();
    if b.dimensions() != (w, h) {
        return Err(PilError::InvalidOperation(
            "images must be same size".into(),
        ));
    }
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let da = a.get_pixel(x, y);
            let sa = b.get_pixel(x, y);
            let src_a = sa[3] as f64 / 255.0;
            let dst_a = da[3] as f64 / 255.0;
            let out_a = src_a + dst_a * (1.0 - src_a);
            if out_a <= 0.0 {
                // Both pixels fully transparent: preserve dst pixel
                out.put_pixel(x, y, *da);
            } else {
                let r = ((sa[0] as f64 * src_a + da[0] as f64 * dst_a * (1.0 - src_a)) / out_a)
                    .round() as u8;
                let g = ((sa[1] as f64 * src_a + da[1] as f64 * dst_a * (1.0 - src_a)) / out_a)
                    .round() as u8;
                let bl = ((sa[2] as f64 * src_a + da[2] as f64 * dst_a * (1.0 - src_a)) / out_a)
                    .round() as u8;
                out.put_pixel(x, y, image::Rgba([r, g, bl, (out_a * 255.0).round() as u8]));
            }
        }
    }
    // If dst was LA/La mode, return LA (2-channel) result
    let dst_mode = mode(dst);
    if dst_mode == "LA" || dst_mode == "La" {
        let la_buf = image::ImageBuffer::from_fn(w, h, |x, y| {
            let p = out.get_pixel(x, y);
            image::LumaA([p[0], p[3]])
        });
        Ok(ImageHandle {
            inner: DynamicImage::ImageLumaA8(la_buf),
            mode_override: Some("LA"),
            palette: None,
            palette_mode: None,
        })
    } else {
        Ok(ImageHandle {
            inner: DynamicImage::ImageRgba8(out),
            mode_override: None,
            palette: None,
            palette_mode: None,
        })
    }
}

// ---------------------------------------------------------------------------
// Bulk pixel access
// ---------------------------------------------------------------------------

/// Return all pixel data as flat Vec of u8 tuples (for getdata)
pub fn getdata(handle: &ImageHandle) -> Vec<Vec<u8>> {
    let rgba = handle.inner.to_rgba8();
    let (w, h) = rgba.dimensions();
    let mode = mode(handle);
    let mut result = Vec::with_capacity((w * h) as usize);
    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y);
            match mode {
                "L" => result.push(vec![p[0]]),
                "LA" => result.push(vec![p[0], p[3]]),
                "RGB" => result.push(vec![p[0], p[1], p[2]]),
                _ => result.push(vec![p[0], p[1], p[2], p[3]]),
            }
        }
    }
    result
}

// ---------------------------------------------------------------------------
// Quantize — median-cut color reduction
// ---------------------------------------------------------------------------

/// Reduce the number of distinct colors in the image.
/// Returns an RGB image with at most `colors` distinct colors.
pub fn quantize(handle: &ImageHandle, max_colors: usize) -> Result<ImageHandle> {
    let rgba = handle.inner.to_rgba8();
    let (w, h) = rgba.dimensions();
    let max_colors = max_colors.clamp(1, 256);

    // Collect all pixel RGB values
    let mut pixels: Vec<[u8; 3]> = Vec::with_capacity((w * h) as usize);
    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y);
            pixels.push([p[0], p[1], p[2]]);
        }
    }

    // Median-cut quantization → palette as RGB triplets
    let palette_rgb = median_cut(&pixels, max_colors);

    // Build flat 256-entry RGB palette (padded with zeros)
    let mut flat_palette = vec![0u8; 256 * 3];
    for (i, rgb) in palette_rgb.iter().enumerate().take(256) {
        flat_palette[i * 3] = rgb[0];
        flat_palette[i * 3 + 1] = rgb[1];
        flat_palette[i * 3 + 2] = rgb[2];
    }

    // Map each pixel to nearest palette index
    let mut out: ImageBuffer<image::Luma<u8>, Vec<u8>> = ImageBuffer::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y);
            let rgb = [p[0], p[1], p[2]];
            let idx = find_nearest_idx(&palette_rgb, &rgb);
            out.put_pixel(x, y, image::Luma([idx as u8]));
        }
    }

    Ok(ImageHandle {
        inner: DynamicImage::ImageLuma8(out),
        mode_override: Some("P"),
        palette: Some(flat_palette),
        palette_mode: Some("RGB".to_string()),
    })
}

fn median_cut(pixels: &[[u8; 3]], max_colors: usize) -> Vec<[u8; 3]> {
    if pixels.is_empty() {
        return vec![[0, 0, 0]];
    }

    let mut buckets: Vec<Vec<[u8; 3]>> = vec![pixels.to_vec()];

    while buckets.len() < max_colors {
        // Find bucket with widest range
        let mut best_idx = 0;
        let mut best_range = 0u16;
        for (i, bucket) in buckets.iter().enumerate() {
            if bucket.len() < 2 {
                continue;
            }
            for ch in 0..3 {
                let mn = bucket.iter().map(|p| p[ch]).min().unwrap_or(0);
                let mx = bucket.iter().map(|p| p[ch]).max().unwrap_or(0);
                let range = (mx as u16) - (mn as u16);
                if range > best_range {
                    best_range = range;
                    best_idx = i;
                }
            }
        }

        if best_range == 0 {
            break;
        }

        let bucket = &buckets[best_idx];
        let mut split_ch = 0;
        let mut split_range = 0u16;
        for ch in 0..3 {
            let mn = bucket.iter().map(|p| p[ch]).min().unwrap_or(0);
            let mx = bucket.iter().map(|p| p[ch]).max().unwrap_or(0);
            let r = (mx as u16) - (mn as u16);
            if r > split_range {
                split_range = r;
                split_ch = ch;
            }
        }

        let mut sorted = buckets.swap_remove(best_idx);
        sorted.sort_by_key(|p| p[split_ch]);
        let mid = sorted.len() / 2;
        let right = sorted.split_off(mid);
        buckets.push(sorted);
        buckets.push(right);
    }

    buckets
        .iter()
        .map(|bucket| {
            if bucket.is_empty() {
                return [0, 0, 0];
            }
            let (mut sr, mut sg, mut sb) = (0u64, 0u64, 0u64);
            for p in bucket {
                sr += p[0] as u64;
                sg += p[1] as u64;
                sb += p[2] as u64;
            }
            let n = bucket.len() as u64;
            [(sr / n) as u8, (sg / n) as u8, (sb / n) as u8]
        })
        .collect()
}

fn find_nearest_idx(palette: &[[u8; 3]], pixel: &[u8; 3]) -> usize {
    let mut best_idx = 0;
    let mut best_dist = u32::MAX;
    for (i, &c) in palette.iter().enumerate() {
        let dr = c[0] as i32 - pixel[0] as i32;
        let dg = c[1] as i32 - pixel[1] as i32;
        let db = c[2] as i32 - pixel[2] as i32;
        let d = (dr * dr + dg * dg + db * db) as u32;
        if d < best_dist {
            best_dist = d;
            best_idx = i;
            if d == 0 {
                break;
            }
        }
    }
    best_idx
}

// ---------------------------------------------------------------------------
// getcolors — return list of (count, color) tuples
// ---------------------------------------------------------------------------

pub fn getcolors(handle: &ImageHandle, maxcolors: usize) -> Option<Vec<(u32, [u8; 4])>> {
    let rgba = handle.inner.to_rgba8();
    let (w, h) = rgba.dimensions();
    let m = mode(handle);
    let channels = match m {
        "L" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };

    let mut counts: std::collections::HashMap<[u8; 4], u32> = std::collections::HashMap::new();
    for y in 0..h {
        for x in 0..w {
            let p = rgba.get_pixel(x, y);
            let key = match channels {
                1 => [p[0], 0, 0, 0],
                2 => [p[0], p[3], 0, 0],
                3 => [p[0], p[1], p[2], 0],
                _ => [p[0], p[1], p[2], p[3]],
            };
            *counts.entry(key).or_insert(0) += 1;
            if counts.len() > maxcolors {
                return None;
            }
        }
    }
    let mut result: Vec<(u32, [u8; 4])> = counts.into_iter().map(|(k, v)| (v, k)).collect();
    result.sort_by(|a, b| b.0.cmp(&a.0));
    Some(result)
}

// ---------------------------------------------------------------------------
// reduce / offset_image / expand_image
// ---------------------------------------------------------------------------

/// Reduce image by integer factor using lanczos downscale.
pub fn reduce(handle: &ImageHandle, factor_x: u32, factor_y: u32) -> ImageHandle {
    let (w, h) = (handle.inner.width(), handle.inner.height());
    let new_w = w.div_ceil(factor_x).max(1);
    let new_h = h.div_ceil(factor_y).max(1);
    let resized = handle
        .inner
        .resize_exact(new_w, new_h, image::imageops::FilterType::Lanczos3);
    ImageHandle {
        inner: resized,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Scroll image cyclically by (x, y) pixels.
pub fn offset_image(handle: &ImageHandle, x: i32, y: i32) -> ImageHandle {
    let w = handle.inner.width() as i32;
    let h = handle.inner.height() as i32;
    if w == 0 || h == 0 {
        return handle.clone();
    }
    let ox = ((x % w) + w) as u32 % w as u32;
    let oy = ((y % h) + h) as u32 % h as u32;
    let img = handle.inner.to_rgba8();
    let mut out = image::RgbaImage::new(w as u32, h as u32);
    for sy in 0..h as u32 {
        for sx in 0..w as u32 {
            let dx = (sx + ox) % w as u32;
            let dy = (sy + oy) % h as u32;
            out.put_pixel(dx, dy, *img.get_pixel(sx, sy));
        }
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &handle.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Add a border of (x, y) pixels around the image filled with color.
pub fn expand_image(handle: &ImageHandle, x: u32, y: u32, color: &[u8]) -> ImageHandle {
    let (w, h) = (handle.inner.width(), handle.inner.height());
    let new_w = w + 2 * x;
    let new_h = h + 2 * y;
    let m = mode(handle);
    let bg = new_image(m, new_w, new_h, color).unwrap_or_else(|_| ImageHandle {
        inner: image::DynamicImage::ImageRgba8(image::RgbaImage::new(new_w, new_h)),
        mode_override: None,
        palette: None,
        palette_mode: None,
    });
    let mut bg = bg;
    paste(&mut bg, handle, x as i32, y as i32, None);
    bg
}

/// Apply pixel = pixel * scale + offset (per-channel) clamped to [0,255].
pub fn point_transform(handle: &ImageHandle, scale: f64, offset: f64) -> ImageHandle {
    let img = handle.inner.to_rgba8();
    let bands = match mode(handle) {
        "L" | "P" => 1usize,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };
    let mut out = img.clone();
    for pixel in out.pixels_mut() {
        for i in 0..bands {
            let v = pixel[i] as f64 * scale + offset;
            pixel[i] = v.clamp(0.0, 255.0) as u8;
        }
    }
    // Convert back to original color space
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &handle.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Apply a 3x4 color matrix transform.
/// matrix is [r_out_coeffs (4), g_out_coeffs (4), b_out_coeffs (4)] = 12 floats for RGB output
pub fn convert_matrix(
    handle: &ImageHandle,
    target_mode: &str,
    matrix: &[f32],
) -> Result<ImageHandle> {
    // For L output, Pillow accepts a 4-element matrix [r_w, g_w, b_w, offset]
    if target_mode == "L" && matrix.len() >= 4 && matrix.len() < 12 {
        let img = handle.inner.to_rgba8();
        let mut out = image::GrayImage::new(img.width(), img.height());
        for (x, y, px) in img.enumerate_pixels() {
            let r = px[0] as f32;
            let g = px[1] as f32;
            let b = px[2] as f32;
            let v =
                (r * matrix[0] + g * matrix[1] + b * matrix[2] + matrix[3]).clamp(0.0, 255.0) as u8;
            out.put_pixel(x, y, image::Luma([v]));
        }
        return Ok(ImageHandle {
            inner: image::DynamicImage::ImageLuma8(out),
            mode_override: None,
            palette: None,
            palette_mode: None,
        });
    }
    if matrix.len() < 12 {
        return Err(PilError::InvalidOperation(
            "matrix must have at least 12 elements".into(),
        ));
    }
    let img = handle.inner.to_rgba8();
    let mut out_rgba = image::RgbaImage::new(img.width(), img.height());
    for (x, y, px) in img.enumerate_pixels() {
        let r = px[0] as f32;
        let g = px[1] as f32;
        let b = px[2] as f32;
        let a = px[3] as f32;
        let nr = r * matrix[0] + g * matrix[1] + b * matrix[2] + matrix[3];
        let ng = r * matrix[4] + g * matrix[5] + b * matrix[6] + matrix[7];
        let nb = r * matrix[8] + g * matrix[9] + b * matrix[10] + matrix[11];
        out_rgba.put_pixel(
            x,
            y,
            image::Rgba([
                nr.clamp(0.0, 255.0) as u8,
                ng.clamp(0.0, 255.0) as u8,
                nb.clamp(0.0, 255.0) as u8,
                a.clamp(0.0, 255.0) as u8,
            ]),
        );
    }
    let di = image::DynamicImage::ImageRgba8(out_rgba);
    let result = match target_mode {
        "L" => image::DynamicImage::ImageLuma8(di.to_luma8()),
        "LA" => image::DynamicImage::ImageLumaA8(di.to_luma_alpha8()),
        "RGB" => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    Ok(ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

/// Histogram restricted to pixels where mask pixel > 0.
pub fn histogram_masked(handle: &ImageHandle, mask: &ImageHandle) -> Vec<u32> {
    let img = handle.inner.to_rgba8();
    let msk = mask.inner.to_luma8();
    let (w, h) = (img.width(), img.height());
    let bands: usize = match mode(handle) {
        "L" | "P" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };
    let mut hist = vec![0u32; 256 * bands];
    for y in 0..h {
        for x in 0..w {
            let mx = x.min(msk.width() - 1);
            let my = y.min(msk.height() - 1);
            if msk.get_pixel(mx, my)[0] == 0 {
                continue;
            }
            let px = img.get_pixel(x, y);
            for b in 0..bands {
                hist[b * 256 + px[b] as usize] += 1;
            }
        }
    }
    hist
}

/// Returns (col_projection, row_projection): non-zero pixel counts per column and per row.
/// For RGB/RGBA images, a pixel is non-zero if any channel > 0.
pub fn getprojection(handle: &ImageHandle) -> (Vec<u32>, Vec<u32>) {
    let (w, h) = (handle.inner.width(), handle.inner.height());
    let img = handle.inner.to_rgba8();
    let bands: usize = match mode(handle) {
        "L" | "P" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4,
    };
    let mut col = vec![0u32; w as usize];
    let mut row = vec![0u32; h as usize];
    for y in 0..h {
        for x in 0..w {
            let px = img.get_pixel(x, y);
            let nonzero = (0..bands).any(|b| px[b] > 0);
            if nonzero {
                col[x as usize] += 1;
                row[y as usize] += 1;
            }
        }
    }
    (col, row)
}

/// Shannon entropy: -sum(p * log2(p)) over histogram.
pub fn entropy(handle: &ImageHandle, mask: Option<&ImageHandle>) -> f64 {
    let hist = match mask {
        Some(m) => histogram_masked(handle, m),
        None => histogram(handle),
    };
    let total: u32 = hist.iter().sum();
    if total == 0 {
        return 0.0;
    }
    let mut e = 0.0f64;
    for &count in &hist {
        if count > 0 {
            let p = count as f64 / total as f64;
            e -= p * p.log2();
        }
    }
    e
}

/// Rank filter: sort pixels in a (size x size) window, return rank-th smallest.
/// Works on L-mode images; RGB images are converted to L first.
pub fn rankfilter(handle: &ImageHandle, size: u32, rank: u32) -> ImageHandle {
    let img = handle.inner.to_luma8();
    let (w, h) = (img.width(), img.height());
    let half = (size / 2) as i32;
    // Input is an expanded image (w = orig_w + size, h = orig_h + size).
    // Output covers input positions half..(w - half) x half..(h - half).
    let out_w = (w as i32 - 2 * half).max(0) as u32;
    let out_h = (h as i32 - 2 * half).max(0) as u32;
    let mut out = image::GrayImage::new(out_w, out_h);
    for oy in 0..out_h as i32 {
        for ox in 0..out_w as i32 {
            let cx = ox + half; // center x in input
            let cy = oy + half; // center y in input
            let mut vals: Vec<u8> = Vec::with_capacity((size * size) as usize);
            for dy in -half..=half {
                for dx in -half..=half {
                    let px = (cx + dx).clamp(0, w as i32 - 1) as u32;
                    let py = (cy + dy).clamp(0, h as i32 - 1) as u32;
                    vals.push(img.get_pixel(px, py)[0]);
                }
            }
            vals.sort_unstable();
            let idx = (rank as usize).min(vals.len().saturating_sub(1));
            out.put_pixel(ox as u32, oy as u32, image::Luma([vals[idx]]));
        }
    }
    let di = image::DynamicImage::ImageLuma8(out);
    ImageHandle {
        inner: di,
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

/// Mode filter: return most common pixel in a (size x size) window.
pub fn modefilter(handle: &ImageHandle, size: u32) -> ImageHandle {
    let img = handle.inner.to_luma8();
    let (w, h) = (img.width(), img.height());
    let half = (size / 2) as i32;
    let mut out = image::GrayImage::new(w, h);
    for y in 0..h as i32 {
        for x in 0..w as i32 {
            let mut counts = [0u32; 256];
            for dy in -half..=half {
                for dx in -half..=half {
                    let px = (x + dx).clamp(0, w as i32 - 1) as u32;
                    let py = (y + dy).clamp(0, h as i32 - 1) as u32;
                    counts[img.get_pixel(px, py)[0] as usize] += 1;
                }
            }
            let mode_val = counts
                .iter()
                .enumerate()
                .max_by_key(|(_, &c)| c)
                .map(|(i, _)| i)
                .unwrap_or(0) as u8;
            out.put_pixel(x as u32, y as u32, image::Luma([mode_val]));
        }
    }
    ImageHandle {
        inner: image::DynamicImage::ImageLuma8(out),
        mode_override: handle.mode_override,
        palette: None,
        palette_mode: None,
    }
}

/// Spread pixels randomly by up to `distance` pixels (deterministic per-pixel hash).
pub fn effect_spread(handle: &ImageHandle, distance: u32) -> ImageHandle {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let img = handle.inner.to_rgba8();
    let (w, h) = (img.width(), img.height());
    let d = distance as i32;
    let mut out = img.clone();
    for y in 0..h as i32 {
        for x in 0..w as i32 {
            let mut hasher = DefaultHasher::new();
            (x, y).hash(&mut hasher);
            let hash = hasher.finish();
            let range = 2 * d + 1;
            let dx = if range > 0 {
                (hash as i32).rem_euclid(range) - d
            } else {
                0
            };
            let dy = if range > 0 {
                ((hash >> 16) as i32).rem_euclid(range) - d
            } else {
                0
            };
            let sx = (x + dx).clamp(0, w as i32 - 1) as u32;
            let sy = (y + dy).clamp(0, h as i32 - 1) as u32;
            out.put_pixel(x as u32, y as u32, *img.get_pixel(sx, sy));
        }
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &handle.inner {
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Splitmix64 finalizer — excellent avalanche properties for per-pixel hashing.
fn splitmix64(x: u64) -> u64 {
    let x = x ^ (x >> 30);
    let x = x.wrapping_mul(0xbf58476d1ce4e5b9);
    let x = x ^ (x >> 27);
    let x = x.wrapping_mul(0x94d049bb133111eb);
    x ^ (x >> 31)
}

/// Generate Gaussian noise centered around 128.
/// Uses per-pixel hash so adjacent pixels have uncorrelated values.
pub fn effect_noise(width: u32, height: u32, sigma: f64) -> ImageHandle {
    use std::f64::consts::PI;
    let buf = image::ImageBuffer::from_fn(width, height, |x, y| {
        let idx = y as u64 * width as u64 + x as u64;
        // Two independent hash values for Box-Muller
        let h1 = splitmix64(idx.wrapping_add(0x9e3779b97f4a7c15));
        let h2 = splitmix64(idx ^ 0x6c62272e07bb0142);
        let u1 = (h1 as f64 + 1.0) / (u64::MAX as f64 + 2.0);
        let u2 = h2 as f64 / (u64::MAX as f64 + 1.0);
        let mag = sigma * (-2.0 * u1.ln()).sqrt();
        let noise = mag * (2.0 * PI * u2).cos();
        let v = (128.0 + noise).clamp(0.0, 255.0) as u8;
        image::Luma([v])
    });
    ImageHandle {
        inner: image::DynamicImage::ImageLuma8(buf),
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Render Mandelbrot set (L mode). Matches Pillow's ImagingEffectMandelbrot exactly.
/// Raises error if quality < 2 or extent width/height < 0.
pub fn effect_mandelbrot(
    width: u32,
    height: u32,
    extent: [f64; 4],
    quality: i32,
) -> Result<ImageHandle> {
    let ext_w = extent[2] - extent[0];
    let ext_h = extent[3] - extent[1];
    if ext_w < 0.0 || ext_h < 0.0 || quality < 2 {
        return Err(PilError::InvalidOperation(
            "bad extent or quality (quality must be ≥ 2, width/height must be ≥ 0)".into(),
        ));
    }
    // Pillow uses (size-1) as divisor so edges map exactly to extent boundaries
    let dr = if width > 1 {
        ext_w / (width - 1) as f64
    } else {
        0.0
    };
    let di = if height > 1 {
        ext_h / (height - 1) as f64
    } else {
        0.0
    };
    let radius = 100.0f64;
    let buf = image::ImageBuffer::from_fn(width, height, |x, y| {
        let cr = x as f64 * dr + extent[0];
        let ci = y as f64 * di + extent[1];
        let mut x1 = 0.0f64;
        let mut y1 = 0.0f64;
        let mut xi2 = 0.0f64;
        let mut yi2 = 0.0f64;
        // Update z FIRST, then check escape (k starts at 1)
        let pixel: u8 = 'outer: {
            let mut k = 1i32;
            loop {
                y1 = 2.0 * x1 * y1 + ci;
                x1 = xi2 - yi2 + cr;
                xi2 = x1 * x1;
                yi2 = y1 * y1;
                if xi2 + yi2 > radius {
                    break 'outer (k * 255 / quality) as u8;
                }
                if k >= quality {
                    break 'outer 0u8; // in set
                }
                k += 1;
            }
        };
        image::Luma([pixel])
    });
    Ok(ImageHandle {
        inner: image::DynamicImage::ImageLuma8(buf),
        mode_override: None,
        palette: None,
        palette_mode: None,
    })
}

// ---------------------------------------------------------------------------
// ImageChops operations
// ---------------------------------------------------------------------------

fn chop_per_pixel<F>(im1: &ImageHandle, im2: &ImageHandle, f: F) -> ImageHandle
where
    F: Fn(u8, u8) -> u8,
{
    let a = im1.inner.to_rgba8();
    let b = im2.inner.to_rgba8();
    let (w, h) = (a.width().min(b.width()), a.height().min(b.height()));
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let pa = a.get_pixel(x, y);
            let pb = b.get_pixel(x, y);
            out.put_pixel(
                x,
                y,
                image::Rgba([f(pa[0], pb[0]), f(pa[1], pb[1]), f(pa[2], pb[2]), pa[3]]),
            );
        }
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &im1.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn chop_add(im1: &ImageHandle, im2: &ImageHandle, scale: f64, offset: f64) -> ImageHandle {
    let a = im1.inner.to_rgba8();
    let b = im2.inner.to_rgba8();
    let (w, h) = (a.width().min(b.width()), a.height().min(b.height()));
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let pa = a.get_pixel(x, y);
            let pb = b.get_pixel(x, y);
            let apply = |a: u8, b: u8| -> u8 {
                ((a as f64 + b as f64) / scale + offset).clamp(0.0, 255.0) as u8
            };
            out.put_pixel(
                x,
                y,
                image::Rgba([
                    apply(pa[0], pb[0]),
                    apply(pa[1], pb[1]),
                    apply(pa[2], pb[2]),
                    pa[3],
                ]),
            );
        }
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &im1.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn chop_subtract(im1: &ImageHandle, im2: &ImageHandle, scale: f64, offset: f64) -> ImageHandle {
    let a = im1.inner.to_rgba8();
    let b = im2.inner.to_rgba8();
    let (w, h) = (a.width().min(b.width()), a.height().min(b.height()));
    let mut out = image::RgbaImage::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let pa = a.get_pixel(x, y);
            let pb = b.get_pixel(x, y);
            let apply = |a: u8, b: u8| -> u8 {
                ((a as f64 - b as f64) / scale + offset).clamp(0.0, 255.0) as u8
            };
            out.put_pixel(
                x,
                y,
                image::Rgba([
                    apply(pa[0], pb[0]),
                    apply(pa[1], pb[1]),
                    apply(pa[2], pb[2]),
                    pa[3],
                ]),
            );
        }
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &im1.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

pub fn chop_add_modulo(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a.wrapping_add(b))
}
pub fn chop_subtract_modulo(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a.wrapping_sub(b))
}
pub fn chop_multiply(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| ((a as u32 * b as u32 + 127) / 255) as u8)
}
pub fn chop_screen(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| {
        (255 - ((255 - a as u32) * (255 - b as u32) / 255)) as u8
    })
}
pub fn chop_difference(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a.abs_diff(b))
}
pub fn chop_darker(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a.min(b))
}
pub fn chop_lighter(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a.max(b))
}
pub fn chop_invert(im: &ImageHandle) -> ImageHandle {
    let a = im.inner.to_rgba8();
    let mut out = a.clone();
    for px in out.pixels_mut() {
        px[0] = 255 - px[0];
        px[1] = 255 - px[1];
        px[2] = 255 - px[2];
    }
    let di = image::DynamicImage::ImageRgba8(out);
    let result = match &im.inner {
        image::DynamicImage::ImageLuma8(_) => image::DynamicImage::ImageLuma8(di.to_luma8()),
        image::DynamicImage::ImageLumaA8(_) => {
            image::DynamicImage::ImageLumaA8(di.to_luma_alpha8())
        }
        image::DynamicImage::ImageRgb8(_) => image::DynamicImage::ImageRgb8(di.to_rgb8()),
        _ => di,
    };
    ImageHandle {
        inner: result,
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}
pub fn chop_and(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a & b)
}
pub fn chop_or(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a | b)
}
pub fn chop_xor(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    chop_per_pixel(im1, im2, |a, b| a ^ b)
}
pub fn chop_soft_light(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    // Pillow C formula (integer arithmetic):
    // ((255-a)*(a*b))/65536 + a*(255 - (255-a)*(255-b)/255)/255
    chop_per_pixel(im1, im2, |a, b| {
        let a = a as i32;
        let b = b as i32;
        let part1 = (255 - a) * (a * b) / 65536;
        let part2 = a * (255 - (255 - a) * (255 - b) / 255) / 255;
        (part1 + part2).clamp(0, 255) as u8
    })
}
pub fn chop_hard_light(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    // Pillow C formula: divide by 127
    chop_per_pixel(im1, im2, |a, b| {
        let a = a as i32;
        let b = b as i32;
        if b < 128 {
            (a * b / 127).clamp(0, 255) as u8
        } else {
            (255 - (255 - b) * (255 - a) / 127).clamp(0, 255) as u8
        }
    })
}
pub fn chop_overlay(im1: &ImageHandle, im2: &ImageHandle) -> ImageHandle {
    // Pillow C formula: divide by 127
    chop_per_pixel(im1, im2, |a, b| {
        let a = a as i32;
        let b = b as i32;
        if a < 128 {
            (a * b / 127).clamp(0, 255) as u8
        } else {
            (255 - (255 - a) * (255 - b) / 127).clamp(0, 255) as u8
        }
    })
}

/// Horizontal linear gradient: L-mode, 256x256, left=0, right=255.
pub fn linear_gradient() -> ImageHandle {
    let mut buf = image::GrayImage::new(256, 256);
    for y in 0..256u32 {
        for x in 0..256u32 {
            buf.put_pixel(x, y, image::Luma([y as u8]));
        }
    }
    ImageHandle {
        inner: image::DynamicImage::ImageLuma8(buf),
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}

/// Radial gradient: L-mode, 256x256, matches Pillow C formula.
/// v = min(255, floor(sqrt((x-128)^2 + (y-128)^2) * sqrt(2)))
pub fn radial_gradient() -> ImageHandle {
    const SQRT2: f64 = std::f64::consts::SQRT_2;
    let mut buf = image::GrayImage::new(256, 256);
    for y in 0..256u32 {
        for x in 0..256u32 {
            let ix = (x as f64) - 128.0;
            let iy = (y as f64) - 128.0;
            let v = ((ix * ix + iy * iy).sqrt() * SQRT2).min(255.0) as u8;
            buf.put_pixel(x, y, image::Luma([v]));
        }
    }
    ImageHandle {
        inner: image::DynamicImage::ImageLuma8(buf),
        mode_override: None,
        palette: None,
        palette_mode: None,
    }
}
