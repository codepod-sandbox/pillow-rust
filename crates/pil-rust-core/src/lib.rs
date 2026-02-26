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
    handle.inner.put_pixel(x, y, image::Rgba(color));
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
        return ImageHandle {
            inner: handle.inner.rotate90(),
        };
    }
    if (deg - 180.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate180(),
        };
    }
    if (deg - 270.0).abs() < 0.5 {
        return ImageHandle {
            inner: handle.inner.rotate270(),
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
        2 => img.rotate90(),
        3 => img.rotate180(),
        4 => img.rotate270(),
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
    x0: u32,
    y0: u32,
    x1: u32,
    y1: u32,
    color: [u8; 4],
    fill: bool,
) {
    let (w, h) = handle.inner.dimensions();
    let x1 = x1.min(w.saturating_sub(1));
    let y1 = y1.min(h.saturating_sub(1));
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
