use image::{DynamicImage, GenericImage, GenericImageView, ImageBuffer, ImageFormat};
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
            PilError::UnsupportedMode(m) => write!(f, "unsupported mode: {m}"),
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
}

impl Clone for ImageHandle {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
        }
    }
}

// ---------------------------------------------------------------------------
// Decode / encode
// ---------------------------------------------------------------------------

pub fn open(bytes: &[u8]) -> Result<ImageHandle> {
    let img = image::load_from_memory(bytes)?;
    Ok(ImageHandle { inner: img })
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
        _ => return Err(PilError::UnsupportedMode(mode.to_string())),
    };
    Ok(ImageHandle { inner: img })
}

pub fn save(handle: &ImageHandle, format: &str) -> Result<Vec<u8>> {
    let fmt = parse_format(format)?;
    let mut buf = Cursor::new(Vec::new());
    handle.inner.write_to(&mut buf, fmt)?;
    Ok(buf.into_inner())
}

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

// ---------------------------------------------------------------------------
// Properties
// ---------------------------------------------------------------------------

pub fn size(handle: &ImageHandle) -> (u32, u32) {
    handle.inner.dimensions()
}

pub fn mode(handle: &ImageHandle) -> &'static str {
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
    handle.inner.as_bytes().to_vec()
}

// ---------------------------------------------------------------------------
// Pixel access
// ---------------------------------------------------------------------------

pub fn getpixel(handle: &ImageHandle, x: u32, y: u32) -> [u8; 4] {
    let p = handle.inner.get_pixel(x, y);
    p.0
}

pub fn putpixel(handle: &mut ImageHandle, x: u32, y: u32, color: [u8; 4]) {
    // For grayscale modes, expand the first channel to all RGB channels
    // so DynamicImage's internal RGBA→Luma conversion preserves the value.
    let pixel = match &handle.inner {
        DynamicImage::ImageLuma8(_) => image::Rgba([color[0], color[0], color[0], 255]),
        DynamicImage::ImageLumaA8(_) => {
            // For LA mode, color comes as [L, A, 0, 255] from Python
            image::Rgba([color[0], color[0], color[0], color[1]])
        }
        _ => image::Rgba(color),
    };
    handle.inner.put_pixel(x, y, pixel);
}

// ---------------------------------------------------------------------------
// Geometric transforms
// ---------------------------------------------------------------------------

pub fn resize(handle: &ImageHandle, w: u32, h: u32, filter: &str) -> ImageHandle {
    let f = parse_filter(filter);
    ImageHandle {
        inner: handle.inner.resize_exact(w, h, f),
    }
}

pub fn crop(handle: &ImageHandle, x: u32, y: u32, w: u32, h: u32) -> ImageHandle {
    ImageHandle {
        inner: handle.inner.crop_imm(x, y, w, h),
    }
}

pub fn rotate(handle: &ImageHandle, degrees: f32) -> ImageHandle {
    let deg = ((degrees % 360.0) + 360.0) % 360.0;

    if (deg - 90.0).abs() < 0.5 {
        // PIL rotate(90) is CCW; image crate rotate270 is CW 270° = CCW 90°
        return ImageHandle {
            inner: handle.inner.rotate270(),
        };
    }
    if (deg - 180.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate180(),
        };
    }
    if (deg - 270.0).abs() < 0.5 {
        // PIL rotate(270) is CCW 270° = CW 90°
        return ImageHandle {
            inner: handle.inner.rotate90(),
        };
    }
    if deg < 0.5 || (360.0 - deg) < 0.5 {
        return ImageHandle {
            inner: handle.inner.clone(),
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
    // Convert back to original mode to preserve it
    let out = match &handle.inner {
        DynamicImage::ImageLuma8(_) => DynamicImage::ImageLuma8(out.to_luma8()),
        DynamicImage::ImageLumaA8(_) => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        DynamicImage::ImageRgb8(_) => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out,
    };
    ImageHandle { inner: out }
}

/// Transpose operations matching PIL constants:
/// 0 = FLIP_LEFT_RIGHT, 1 = FLIP_TOP_BOTTOM, 2 = ROTATE_90,
/// 3 = ROTATE_180, 4 = ROTATE_270, 5 = TRANSPOSE, 6 = TRANSVERSE
pub fn transpose(handle: &ImageHandle, method: u8) -> Result<ImageHandle> {
    let img = &handle.inner;
    let out = match method {
        0 => img.fliph(),
        1 => img.flipv(),
        // PIL ROTATE_90 is CCW 90° = image crate CW 270°
        2 => img.rotate270(),
        3 => img.rotate180(),
        // PIL ROTATE_270 is CCW 270° = image crate CW 90°
        4 => img.rotate90(),
        5 => {
            // TRANSPOSE = flip along main diagonal (swap x/y then flip)
            let rotated = img.rotate90();
            rotated.fliph()
        }
        6 => {
            // TRANSVERSE = flip along anti-diagonal
            let rotated = img.rotate90();
            rotated.flipv()
        }
        _ => {
            return Err(PilError::InvalidOperation(format!(
                "unknown transpose method: {method}"
            )))
        }
    };
    Ok(ImageHandle { inner: out })
}

// ---------------------------------------------------------------------------
// Mode conversion
// ---------------------------------------------------------------------------

pub fn convert(handle: &ImageHandle, target_mode: &str) -> Result<ImageHandle> {
    let img = match target_mode {
        "RGB" => DynamicImage::ImageRgb8(handle.inner.to_rgb8()),
        "RGBA" => DynamicImage::ImageRgba8(handle.inner.to_rgba8()),
        "L" => DynamicImage::ImageLuma8(handle.inner.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(handle.inner.to_luma_alpha8()),
        _ => return Err(PilError::UnsupportedMode(target_mode.to_string())),
    };
    Ok(ImageHandle { inner: img })
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
        _ => {
            return Err(PilError::InvalidOperation(format!(
                "unknown filter: {name}"
            )))
        }
    };
    Ok(ImageHandle { inner: out })
}

// ---------------------------------------------------------------------------
// Drawing
// ---------------------------------------------------------------------------

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
    let pixel = image::Rgba(color);

    if fill {
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                handle.inner.put_pixel(x, y, pixel);
            }
        }
    } else {
        // Top and bottom edges
        for x in min_x..=max_x {
            if min_y < h {
                handle.inner.put_pixel(x, min_y, pixel);
            }
            if max_y < h {
                handle.inner.put_pixel(x, max_y, pixel);
            }
        }
        // Left and right edges
        for y in min_y..=max_y {
            if min_x < w {
                handle.inner.put_pixel(min_x, y, pixel);
            }
            if max_x < w {
                handle.inner.put_pixel(max_x, y, pixel);
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
    let pixel = image::Rgba(color);
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
    let pixel = image::Rgba(color);
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
    let pixel = image::Rgba(color);

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
    let rgba = handle.inner.to_rgba8();
    let (w, h) = handle.inner.dimensions();
    let mut sum: f64 = 0.0;
    let mut count: u64 = 0;
    for px in rgba.pixels() {
        let lum = 0.299 * px[0] as f64 + 0.587 * px[1] as f64 + 0.114 * px[2] as f64;
        sum += lum;
        count += 1;
    }
    let mean = if count > 0 {
        (sum / count as f64).round() as u8
    } else {
        128
    };

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
// frombytes — create image from raw pixel bytes
// ---------------------------------------------------------------------------

pub fn frombytes(mode: &str, width: u32, height: u32, data: &[u8]) -> Result<ImageHandle> {
    let img = match mode {
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
        _ => return Err(PilError::UnsupportedMode(mode.to_string())),
    };
    Ok(ImageHandle { inner: img })
}

// ---------------------------------------------------------------------------
// split — extract individual channels as grayscale images
// ---------------------------------------------------------------------------

pub fn split(handle: &ImageHandle) -> Vec<ImageHandle> {
    match &handle.inner {
        DynamicImage::ImageLuma8(buf) => {
            vec![ImageHandle {
                inner: DynamicImage::ImageLuma8(buf.clone()),
            }]
        }
        DynamicImage::ImageLumaA8(buf) => {
            let (w, h) = buf.dimensions();
            let mut l_buf = ImageBuffer::new(w, h);
            let mut a_buf = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                l_buf.put_pixel(x, y, image::Luma([px[0]]));
                a_buf.put_pixel(x, y, image::Luma([px[1]]));
            }
            vec![
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(l_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(a_buf),
                },
            ]
        }
        DynamicImage::ImageRgb8(buf) => {
            let (w, h) = buf.dimensions();
            let mut r_buf = ImageBuffer::new(w, h);
            let mut g_buf = ImageBuffer::new(w, h);
            let mut b_buf = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                r_buf.put_pixel(x, y, image::Luma([px[0]]));
                g_buf.put_pixel(x, y, image::Luma([px[1]]));
                b_buf.put_pixel(x, y, image::Luma([px[2]]));
            }
            vec![
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(r_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(g_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(b_buf),
                },
            ]
        }
        DynamicImage::ImageRgba8(buf) => {
            let (w, h) = buf.dimensions();
            let mut r_buf = ImageBuffer::new(w, h);
            let mut g_buf = ImageBuffer::new(w, h);
            let mut b_buf = ImageBuffer::new(w, h);
            let mut a_buf = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                r_buf.put_pixel(x, y, image::Luma([px[0]]));
                g_buf.put_pixel(x, y, image::Luma([px[1]]));
                b_buf.put_pixel(x, y, image::Luma([px[2]]));
                a_buf.put_pixel(x, y, image::Luma([px[3]]));
            }
            vec![
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(r_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(g_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(b_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(a_buf),
                },
            ]
        }
        _ => {
            // Fallback: convert to RGBA and split
            let rgba = handle.inner.to_rgba8();
            let (w, h) = rgba.dimensions();
            let mut r_buf = ImageBuffer::new(w, h);
            let mut g_buf = ImageBuffer::new(w, h);
            let mut b_buf = ImageBuffer::new(w, h);
            let mut a_buf = ImageBuffer::new(w, h);
            for (x, y, px) in rgba.enumerate_pixels() {
                r_buf.put_pixel(x, y, image::Luma([px[0]]));
                g_buf.put_pixel(x, y, image::Luma([px[1]]));
                b_buf.put_pixel(x, y, image::Luma([px[2]]));
                a_buf.put_pixel(x, y, image::Luma([px[3]]));
            }
            vec![
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(r_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(g_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(b_buf),
                },
                ImageHandle {
                    inner: DynamicImage::ImageLuma8(a_buf),
                },
            ]
        }
    }
}

// ---------------------------------------------------------------------------
// merge — combine grayscale channels into a multi-channel image
// ---------------------------------------------------------------------------

pub fn merge(target_mode: &str, channels: &[&ImageHandle]) -> Result<ImageHandle> {
    let (w, h) = channels
        .first()
        .map(|c| c.inner.dimensions())
        .unwrap_or((0, 0));

    let img = match target_mode {
        "L" => {
            if channels.len() != 1 {
                return Err(PilError::InvalidOperation(
                    "L mode requires 1 channel".into(),
                ));
            }
            DynamicImage::ImageLuma8(channels[0].inner.to_luma8())
        }
        "LA" => {
            if channels.len() != 2 {
                return Err(PilError::InvalidOperation(
                    "LA mode requires 2 channels".into(),
                ));
            }
            let l = channels[0].inner.to_luma8();
            let a = channels[1].inner.to_luma8();
            let mut buf = ImageBuffer::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    buf.put_pixel(
                        x,
                        y,
                        image::LumaA([l.get_pixel(x, y)[0], a.get_pixel(x, y)[0]]),
                    );
                }
            }
            DynamicImage::ImageLumaA8(buf)
        }
        "RGB" => {
            if channels.len() != 3 {
                return Err(PilError::InvalidOperation(
                    "RGB mode requires 3 channels".into(),
                ));
            }
            let r = channels[0].inner.to_luma8();
            let g = channels[1].inner.to_luma8();
            let b = channels[2].inner.to_luma8();
            let mut buf = ImageBuffer::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    buf.put_pixel(
                        x,
                        y,
                        image::Rgb([
                            r.get_pixel(x, y)[0],
                            g.get_pixel(x, y)[0],
                            b.get_pixel(x, y)[0],
                        ]),
                    );
                }
            }
            DynamicImage::ImageRgb8(buf)
        }
        "RGBA" => {
            if channels.len() != 4 {
                return Err(PilError::InvalidOperation(
                    "RGBA mode requires 4 channels".into(),
                ));
            }
            let r = channels[0].inner.to_luma8();
            let g = channels[1].inner.to_luma8();
            let b = channels[2].inner.to_luma8();
            let a = channels[3].inner.to_luma8();
            let mut buf = ImageBuffer::new(w, h);
            for y in 0..h {
                for x in 0..w {
                    buf.put_pixel(
                        x,
                        y,
                        image::Rgba([
                            r.get_pixel(x, y)[0],
                            g.get_pixel(x, y)[0],
                            b.get_pixel(x, y)[0],
                            a.get_pixel(x, y)[0],
                        ]),
                    );
                }
            }
            DynamicImage::ImageRgba8(buf)
        }
        _ => return Err(PilError::UnsupportedMode(target_mode.to_string())),
    };
    Ok(ImageHandle { inner: img })
}

// ---------------------------------------------------------------------------
// paste — paste one image onto another
// ---------------------------------------------------------------------------

pub fn paste(dest: &mut ImageHandle, src: &ImageHandle, x: i32, y: i32) {
    let (dw, dh) = dest.inner.dimensions();
    let (sw, sh) = src.inner.dimensions();

    for sy in 0..sh {
        for sx in 0..sw {
            let dx = x + sx as i32;
            let dy = y + sy as i32;
            if dx >= 0 && dx < dw as i32 && dy >= 0 && dy < dh as i32 {
                let pixel = src.inner.get_pixel(sx, sy);
                dest.inner.put_pixel(dx as u32, dy as u32, pixel);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// getbbox — bounding box of non-zero region
// ---------------------------------------------------------------------------

pub fn getbbox(handle: &ImageHandle) -> Option<(u32, u32, u32, u32)> {
    let (w, h) = handle.inner.dimensions();
    if w == 0 || h == 0 {
        return None;
    }
    let mut min_x = w;
    let mut min_y = h;
    let mut max_x = 0u32;
    let mut max_y = 0u32;

    // Determine how many channels are meaningful (ignore alpha for non-alpha modes)
    let check_channels: usize = match &handle.inner {
        DynamicImage::ImageLuma8(_) => 1,
        DynamicImage::ImageLumaA8(_) => 1, // only check L, not A
        DynamicImage::ImageRgb8(_) => 3,
        DynamicImage::ImageRgba8(_) => 3, // only check RGB, not A
        _ => 3,
    };

    for y in 0..h {
        for x in 0..w {
            let p = handle.inner.get_pixel(x, y);
            let is_zero = p.0[..check_channels].iter().all(|&v| v == 0);
            if !is_zero {
                min_x = min_x.min(x);
                min_y = min_y.min(y);
                max_x = max_x.max(x);
                max_y = max_y.max(y);
            }
        }
    }

    if min_x > max_x {
        None
    } else {
        Some((min_x, min_y, max_x + 1, max_y + 1))
    }
}

// ---------------------------------------------------------------------------
// putdata — set all pixels from a flat byte slice
// ---------------------------------------------------------------------------

pub fn putdata(handle: &mut ImageHandle, data: &[u8]) {
    let (w, h) = handle.inner.dimensions();
    let bands = match &handle.inner {
        DynamicImage::ImageLuma8(_) => 1,
        DynamicImage::ImageLumaA8(_) => 2,
        DynamicImage::ImageRgb8(_) => 3,
        DynamicImage::ImageRgba8(_) => 4,
        _ => 3,
    };
    let mut idx = 0usize;
    for y in 0..h {
        for x in 0..w {
            if idx + bands > data.len() {
                return;
            }
            let color = match bands {
                1 => [data[idx], data[idx], data[idx], 255],
                2 => [data[idx], data[idx], data[idx], data[idx + 1]],
                3 => [data[idx], data[idx + 1], data[idx + 2], 255],
                4 => [data[idx], data[idx + 1], data[idx + 2], data[idx + 3]],
                _ => [0, 0, 0, 255],
            };
            putpixel(handle, x, y, color);
            idx += bands;
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
            })
        }
        DynamicImage::ImageRgb8(buf) => {
            if lut.len() < 768 {
                return Err(PilError::InvalidOperation("LUT too short for RGB".into()));
            }
            let mut out = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(
                    x,
                    y,
                    image::Rgb([
                        lut[px[0] as usize],
                        lut[256 + px[1] as usize],
                        lut[512 + px[2] as usize],
                    ]),
                );
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgb8(out),
            })
        }
        DynamicImage::ImageRgba8(buf) => {
            if lut.len() < 1024 {
                return Err(PilError::InvalidOperation("LUT too short for RGBA".into()));
            }
            let mut out = ImageBuffer::new(w, h);
            for (x, y, px) in buf.enumerate_pixels() {
                out.put_pixel(
                    x,
                    y,
                    image::Rgba([
                        lut[px[0] as usize],
                        lut[256 + px[1] as usize],
                        lut[512 + px[2] as usize],
                        lut[768 + px[3] as usize],
                    ]),
                );
            }
            Ok(ImageHandle {
                inner: DynamicImage::ImageRgba8(out),
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
