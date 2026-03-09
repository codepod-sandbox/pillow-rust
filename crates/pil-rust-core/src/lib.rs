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
    // Write in the image's native format to avoid mode corruption
    match &mut handle.inner {
        DynamicImage::ImageLuma8(buf) => {
            buf.put_pixel(x, y, image::Luma([color[0]]));
        }
        DynamicImage::ImageLumaA8(buf) => {
            buf.put_pixel(x, y, image::LumaA([color[0], color[3]]));
        }
        DynamicImage::ImageRgb8(buf) => {
            buf.put_pixel(x, y, image::Rgb([color[0], color[1], color[2]]));
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

    // PIL rotates CCW; image crate rotates CW — swap 90↔270
    if (deg - 90.0).abs() < 0.5 {
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
    // Convert back to original mode so rotation preserves mode
    let out = match mode(handle) {
        "L" => DynamicImage::ImageLuma8(out.to_luma8()),
        "LA" => DynamicImage::ImageLumaA8(out.to_luma_alpha8()),
        "RGB" => DynamicImage::ImageRgb8(out.to_rgb8()),
        _ => out, // RGBA already
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
    let x0 = x0.max(0) as u32;
    let y0 = y0.max(0) as u32;
    let x1 = (x1.max(0) as u32).min(w.saturating_sub(1));
    let y1 = (y1.max(0) as u32).min(h.saturating_sub(1));
    let pixel = image::Rgba(color);

    if fill {
        for y in y0..=y1 {
            for x in x0..=x1 {
                handle.inner.put_pixel(x, y, pixel);
            }
        }
    } else {
        // Top and bottom edges
        for x in x0..=x1 {
            if y0 < h {
                handle.inner.put_pixel(x, y0, pixel);
            }
            if y1 < h {
                handle.inner.put_pixel(x, y1, pixel);
            }
        }
        // Left and right edges
        for y in y0..=y1 {
            if x0 < w {
                handle.inner.put_pixel(x0, y, pixel);
            }
            if x1 < w {
                handle.inner.put_pixel(x1, y, pixel);
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
        if code < 32 || code > 126 {
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
    let rgba = handle.inner.to_rgba8();

    let mut channels = Vec::new();
    let num = match mode(handle) {
        "L" => 1,
        "LA" => 2,
        "RGB" => 3,
        _ => 4, // RGBA
    };

    for ch in 0..num {
        let idx = if mode(handle) == "LA" && ch == 1 {
            3
        } else {
            ch
        }; // LA: luminance + alpha
        let buf = ImageBuffer::from_fn(w, h, |x, y| image::Luma([rgba.get_pixel(x, y).0[idx]]));
        channels.push(ImageHandle {
            inner: DynamicImage::ImageLuma8(buf),
        });
    }
    channels
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
            if channels.len() < 1 {
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
        _ => return Err(PilError::UnsupportedMode(target_mode.to_string())),
    };
    Ok(ImageHandle { inner: img })
}

// ---------------------------------------------------------------------------
// Statistics / analysis
// ---------------------------------------------------------------------------

pub fn histogram(handle: &ImageHandle) -> Vec<u32> {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
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

    for y in 0..h {
        for x in 0..w {
            let p = handle.inner.get_pixel(x, y).0;
            let nonzero = p[0] != 0 || p[1] != 0 || p[2] != 0;
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
        _ => return Err(PilError::UnsupportedMode(mode_str.to_string())),
    };
    Ok(ImageHandle { inner: img })
}

// ---------------------------------------------------------------------------
// Drawing: polygon, arc, pieslice
// ---------------------------------------------------------------------------

pub fn draw_polygon(handle: &mut ImageHandle, points: &[(i32, i32)], color: [u8; 4], fill: bool) {
    if points.len() < 2 {
        return;
    }
    let (w, h) = handle.inner.dimensions();
    let pixel = image::Rgba(color);

    if fill && points.len() >= 3 {
        // Scanline fill
        let mut min_y = i32::MAX;
        let mut max_y = i32::MIN;
        for &(_, y) in points {
            min_y = min_y.min(y);
            max_y = max_y.max(y);
        }
        min_y = min_y.max(0);
        max_y = max_y.min(h as i32 - 1);

        for y in min_y..=max_y {
            let mut nodes = Vec::new();
            let n = points.len();
            for i in 0..n {
                let j = (i + 1) % n;
                let (_, y0) = points[i];
                let (_, y1) = points[j];
                if (y0 <= y && y1 > y) || (y1 <= y && y0 > y) {
                    let x0 = points[i].0 as f64;
                    let x1 = points[j].0 as f64;
                    let t = (y as f64 - y0 as f64) / (y1 as f64 - y0 as f64);
                    nodes.push((x0 + t * (x1 - x0)) as i32);
                }
            }
            nodes.sort_unstable();
            for pair in nodes.chunks(2) {
                if pair.len() == 2 {
                    let x_start = pair[0].max(0);
                    let x_end = pair[1].min(w as i32 - 1);
                    for x in x_start..=x_end {
                        handle.inner.put_pixel(x as u32, y as u32, pixel);
                    }
                }
            }
        }
    }

    // Draw outline
    let n = points.len();
    for i in 0..n {
        let j = (i + 1) % n;
        draw_line(
            handle,
            points[i].0,
            points[i].1,
            points[j].0,
            points[j].1,
            color,
            1,
        );
    }
}

pub fn draw_arc(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    start: f64,
    end: f64,
    color: [u8; 4],
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

    let steps = ((rx + ry) * 2.0) as usize;
    let steps = steps.max(100);
    let start_rad = start.to_radians();
    let end_rad = end.to_radians();
    let mut angle = start_rad;
    let step = (end_rad - start_rad) / steps as f64;

    for _ in 0..=steps {
        let px = (cx + rx * angle.cos()).round() as i32;
        let py = (cy + ry * angle.sin()).round() as i32;
        if px >= 0 && px < w as i32 && py >= 0 && py < h as i32 {
            handle.inner.put_pixel(px as u32, py as u32, pixel);
        }
        angle += step;
    }
}

pub fn draw_pieslice(
    handle: &mut ImageHandle,
    x0: i32,
    y0: i32,
    x1: i32,
    y1: i32,
    start: f64,
    end: f64,
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

    if fill {
        // Build polygon: center + arc points + center
        let steps = ((rx + ry) * 2.0) as usize;
        let steps = steps.max(100);
        let start_rad = start.to_radians();
        let end_rad = end.to_radians();
        let step = (end_rad - start_rad) / steps as f64;

        let mut points = vec![(cx.round() as i32, cy.round() as i32)];
        let mut angle = start_rad;
        for _ in 0..=steps {
            let px = (cx + rx * angle.cos()).round() as i32;
            let py = (cy + ry * angle.sin()).round() as i32;
            points.push((px, py));
            angle += step;
        }
        points.push((cx.round() as i32, cy.round() as i32));
        draw_polygon(handle, &points, color, true);
    } else {
        // Draw arc + two lines from center to arc endpoints
        draw_arc(handle, x0, y0, x1, y1, start, end, color);
        let start_rad = start.to_radians();
        let end_rad = end.to_radians();
        let cxi = cx.round() as i32;
        let cyi = cy.round() as i32;
        let sx = (cx + rx * start_rad.cos()).round() as i32;
        let sy = (cy + ry * start_rad.sin()).round() as i32;
        let ex = (cx + rx * end_rad.cos()).round() as i32;
        let ey = (cy + ry * end_rad.sin()).round() as i32;
        draw_line(handle, cxi, cyi, sx, sy, color, 1);
        draw_line(handle, cxi, cyi, ex, ey, color, 1);
    }
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
        let clamp = |v: f32| -> u8 { v.round().max(0.0).min(255.0) as u8 };
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
    ImageHandle { inner: img }
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
        let clamp = |v: f32| -> u8 { v.round().max(0.0).min(255.0) as u8 };
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
    ImageHandle { inner: img }
}

pub fn adjust_color(handle: &ImageHandle, factor: f32) -> ImageHandle {
    let (w, h) = handle.inner.dimensions();
    let m = mode(handle);
    let rgba = handle.inner.to_rgba8();
    let gray = handle.inner.to_luma8();
    let out = ImageBuffer::from_fn(w, h, |x, y| {
        let p = rgba.get_pixel(x, y).0;
        let g = gray.get_pixel(x, y).0[0];
        let clamp = |v: f32| -> u8 { v.round().max(0.0).min(255.0) as u8 };
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
    ImageHandle { inner: img }
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
        let clamp = |v: f32| -> u8 { v.round().max(0.0).min(255.0) as u8 };
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
    ImageHandle { inner: img }
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
    ImageHandle { inner: img }
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
    ImageHandle { inner: img }
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

fn parse_filter(filter: &str) -> image::imageops::FilterType {
    match filter.to_ascii_lowercase().as_str() {
        "nearest" | "0" => image::imageops::FilterType::Nearest,
        "bilinear" | "linear" | "2" => image::imageops::FilterType::Triangle,
        "bicubic" | "cubic" | "3" => image::imageops::FilterType::CatmullRom,
        "lanczos" | "1" => image::imageops::FilterType::Lanczos3,
        _ => image::imageops::FilterType::Triangle,
    }
}
