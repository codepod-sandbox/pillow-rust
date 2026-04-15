use pyo3::prelude::*;

mod font;
mod imaging_core;
mod imaging_draw;
mod imaging_path;
mod pixel_access;

use font::Font;
use imaging_core::ImagingCore;
use imaging_draw::ImagingDraw;
use imaging_path::{ImagingOutline, ImagingPath};
use pixel_access::PixelAccess;

#[pyfunction]
#[pyo3(signature = (im, blend=None))]
fn draw(im: Py<imaging_core::ImagingCore>, blend: Option<i32>) -> imaging_draw::ImagingDraw {
    let _ = blend;
    imaging_draw::ImagingDraw { im }
}

fn extract_size(size: &Bound<'_, PyAny>) -> PyResult<(u32, u32)> {
    if let Ok((w, h)) = size.extract::<(i32, i32)>() {
        if w < 0 || h < 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "image size must be positive",
            ));
        }
        return Ok((w as u32, h as u32));
    }
    if let Ok(v) = size.extract::<Vec<i32>>() {
        if v.len() >= 2 {
            let w = v[0];
            let h = v[1];
            if w < 0 || h < 0 {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "image size must be positive",
                ));
            }
            return Ok((w as u32, h as u32));
        }
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "size must be a 2-tuple or 2-element list of ints",
    ))
}

#[pyfunction]
fn new(mode: &str, size: &Bound<'_, PyAny>) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    let handle = pil_rust_core::new_image(mode, w, h, &[0, 0, 0, 0])
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn fill(
    mode: &str,
    size: &Bound<'_, PyAny>,
    color: &Bound<'_, PyAny>,
) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    let bytes = extract_color_bytes(color, mode)?;
    let handle = pil_rust_core::new_image(mode, w, h, &bytes)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

pub fn extract_color_bytes(color: &Bound<'_, PyAny>, mode: &str) -> PyResult<Vec<u8>> {
    // An int larger than the largest supported pixel value raises OverflowError
    // in Pillow (e.g. 2**80 on any mode). Check this before the normal extraction
    // path so we don't silently truncate via f64 casts.
    if color.cast::<pyo3::types::PyInt>().is_ok() && color.extract::<i64>().is_err() {
        return Err(pyo3::exceptions::PyOverflowError::new_err(
            "color value out of range",
        ));
    }
    // For 16-bit integer modes (stored as Luma16), a scalar int should be split into LE bytes
    let is_16bit = matches!(mode, "I" | "F" | "I;16" | "I;16L" | "I;16B" | "I;16N");
    if is_16bit {
        if let Ok(v) = color.extract::<u32>() {
            let lo = (v & 0xFF) as u8;
            let hi = ((v >> 8) & 0xFF) as u8;
            return Ok(vec![lo, hi, 0, 255]);
        }
        if let Ok(t) = color.extract::<(u32,)>() {
            let lo = (t.0 & 0xFF) as u8;
            let hi = ((t.0 >> 8) & 0xFF) as u8;
            return Ok(vec![lo, hi, 0, 255]);
        }
    }
    // Helper: number of channels for a mode (used for scalar expansion).
    // Modes with an alpha channel get alpha = same scalar value (Pillow compat).
    let n_channels = match mode {
        "L" | "P" => 1usize,
        "LA" | "PA" => 2,
        "RGB" => 3,
        "RGBA" => 4,
        _ => 4, // safe default — underlying storage is always 4 bytes
    };
    // Scalar u8: expand to all channels (including alpha if present)
    if let Ok(v) = color.extract::<u8>() {
        let alpha = if n_channels >= 4 { v } else { 255 };
        return Ok(vec![v, v, v, alpha]);
    }
    if let Ok(v) = color.extract::<f64>() {
        let b = v.clamp(0.0, 255.0) as u8;
        let alpha = if n_channels >= 4 { b } else { 255 };
        return Ok(vec![b, b, b, alpha]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8, u8)>() {
        return Ok(vec![t.0, t.1, t.2, t.3]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8)>() {
        return Ok(vec![t.0, t.1, t.2, 255]);
    }
    if let Ok(t) = color.extract::<(u8, u8)>() {
        // LA tuple: color[0]=L, color[1]=A (putpixel reads [0] and [1] for LumaA)
        return Ok(vec![t.0, t.1, t.0, t.1]);
    }
    // 1-element tuple e.g. (5,) — treat as grayscale
    if let Ok(v) = color.extract::<Vec<u8>>() {
        if let Some(&b) = v.first() {
            let alpha = if n_channels >= 4 { b } else { 255 };
            return Ok(vec![b, b, b, alpha]);
        }
    }
    if let Ok(v) = color.extract::<i32>() {
        // Packed RGB integer (e.g. 0xFF0000 for red) — alpha stays 255
        // unless mode is RGBA and v fits in a single byte (0..=255), in
        // which case it means "all channels = v" just like a scalar u8.
        if n_channels >= 4 && (0..=255).contains(&v) {
            let b = v as u8;
            return Ok(vec![b, b, b, b]);
        }
        return Ok(vec![
            ((v >> 16) & 0xFF) as u8,
            ((v >> 8) & 0xFF) as u8,
            (v & 0xFF) as u8,
            255,
        ]);
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "cannot extract color",
    ))
}

#[pyfunction]
#[pyo3(signature = (mode, *bands))]
fn merge(
    mode: &str,
    bands: Vec<PyRef<'_, imaging_core::ImagingCore>>,
) -> PyResult<imaging_core::ImagingCore> {
    let handles: Vec<&pil_rust_core::ImageHandle> = bands.iter().map(|b| &b.handle).collect();
    let handle = pil_rust_core::merge(mode, &handles)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn blend(
    im1: &imaging_core::ImagingCore,
    im2: &imaging_core::ImagingCore,
    alpha: f64,
) -> PyResult<imaging_core::ImagingCore> {
    let handle = pil_rust_core::blend(&im1.handle, &im2.handle, alpha)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
#[pyo3(name = "alpha_composite")]
fn alpha_composite_module(
    dst: &imaging_core::ImagingCore,
    src: &imaging_core::ImagingCore,
) -> PyResult<imaging_core::ImagingCore> {
    let handle = pil_rust_core::alpha_composite(&dst.handle, &src.handle)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn linear_gradient(mode: &str) -> PyResult<imaging_core::ImagingCore> {
    if !matches!(mode, "L" | "P" | "I" | "F") {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "mode must be L, P, I or F, not {mode}"
        )));
    }
    let l_handle = pil_rust_core::linear_gradient();
    let handle = pil_rust_core::convert(&l_handle, mode)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn radial_gradient(mode: &str) -> PyResult<imaging_core::ImagingCore> {
    if !matches!(mode, "L" | "P" | "I" | "F") {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "mode must be L, P, I or F, not {mode}"
        )));
    }
    let l_handle = pil_rust_core::radial_gradient();
    let handle = pil_rust_core::convert(&l_handle, mode)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn open_from_bytes(data: &[u8]) -> PyResult<imaging_core::ImagingCore> {
    let handle = pil_rust_core::open(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
#[pyo3(signature = (frames, delays_ms, loop_count=0))]
fn gif_save_animated<'py>(
    frames: Vec<PyRef<'_, imaging_core::ImagingCore>>,
    delays_ms: Vec<u32>,
    loop_count: u16,
    py: Python<'py>,
) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
    let handles: Vec<&pil_rust_core::ImageHandle> = frames.iter().map(|f| &f.handle).collect();
    let data = pil_rust_core::gif_save_animated(&handles, &delays_ms, loop_count)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &data))
}

/// Save one or more palette-indexed frames with an explicit colour table.
/// `pixel_frames` is a list of raw palette-index bytes (one byte per pixel),
/// `palette_bytes` is the flat RGB colour table (3 bytes per entry, ≤ 256 entries).
#[pyfunction]
#[pyo3(signature = (pixel_frames, width, height, palette_bytes, delays_ms, loop_count=0))]
fn gif_save_with_palette<'py>(
    pixel_frames: Vec<Vec<u8>>,
    width: u16,
    height: u16,
    palette_bytes: Vec<u8>,
    delays_ms: Vec<u32>,
    loop_count: u16,
    py: Python<'py>,
) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
    let refs: Vec<&[u8]> = pixel_frames.iter().map(|v| v.as_slice()).collect();
    let data = pil_rust_core::gif_save_with_palette(
        &refs,
        width,
        height,
        &palette_bytes,
        &delays_ms,
        loop_count,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &data))
}

#[pyfunction]
fn gif_decode_frame(data: &[u8], frame_idx: usize) -> PyResult<imaging_core::ImagingCore> {
    let handle = pil_rust_core::gif_decode_frame(data, frame_idx)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn gif_frame_count(data: &[u8]) -> PyResult<usize> {
    pil_rust_core::gif_frame_count(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
}

#[pyfunction]
#[pyo3(signature = (im, format, **kwargs))]
fn save_to_bytes<'py>(
    im: &imaging_core::ImagingCore,
    format: &str,
    kwargs: Option<&Bound<'py, pyo3::types::PyDict>>,
    py: Python<'py>,
) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
    // Extract quality from kwargs (used for JPEG)
    let quality: Option<u8> = kwargs.and_then(|kw| {
        kw.get_item("quality")
            .ok()
            .flatten()
            .and_then(|v| v.extract::<u8>().ok())
    });
    // Extract optimize from kwargs (used for GIF).  Default: true (matches
    // GifImagePlugin's encoderinfo.setdefault("optimize", True) behaviour).
    let optimize: bool = kwargs
        .and_then(|kw| kw.get_item("optimize").ok().flatten())
        .map(|v| {
            if let Ok(b) = v.extract::<bool>() {
                b
            } else if let Ok(i) = v.extract::<i64>() {
                i != 0
            } else {
                true
            }
        })
        .unwrap_or(true);
    let data = pil_rust_core::save_with_options(
        &im.handle,
        &format.to_ascii_lowercase(),
        quality,
        optimize,
    )
    .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &data))
}

#[pyfunction]
#[pyo3(signature = (coords=None))]
fn path(coords: Option<&Bound<'_, PyAny>>) -> PyResult<imaging_path::ImagingPath> {
    let Some(coords) = coords else {
        return Ok(imaging_path::ImagingPath { coords: vec![] });
    };
    let pts: Vec<(f64, f64)> = if let Ok(flat) = coords.extract::<Vec<f64>>() {
        if flat.len() % 2 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "incorrect number of coordinates",
            ));
        }
        flat.chunks(2).map(|c| (c[0], c[1])).collect()
    } else if let Ok(pairs) = coords.extract::<Vec<(f64, f64)>>() {
        pairs
    } else {
        return Err(pyo3::exceptions::PyTypeError::new_err(
            "path coords must be flat list or list of pairs",
        ));
    };
    Ok(imaging_path::ImagingPath { coords: pts })
}

#[pyfunction]
fn new_block(mode: &str, size: &Bound<'_, PyAny>) -> PyResult<imaging_core::ImagingCore> {
    new(mode, size)
}

#[pyfunction]
fn outline() -> imaging_path::ImagingOutline {
    imaging_path::ImagingOutline::new()
}

#[pyfunction]
#[pyo3(signature = (size, extent, quality))]
fn effect_mandelbrot(
    size: &Bound<'_, PyAny>,
    extent: &Bound<'_, PyAny>,
    quality: i32,
) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    // extent must be a 4-element sequence of floats
    let ext_vec: Vec<f64> = extent.extract::<Vec<f64>>().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err("extent must be a 4-element sequence")
    })?;
    if ext_vec.len() != 4 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "extent must have exactly 4 elements",
        ));
    }
    let ext = [ext_vec[0], ext_vec[1], ext_vec[2], ext_vec[3]];
    let handle = pil_rust_core::effect_mandelbrot(w, h, ext, quality)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
#[pyo3(signature = (size, sigma))]
fn effect_noise(size: &Bound<'_, PyAny>, sigma: f64) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    let handle = pil_rust_core::effect_noise(w, h, sigma);
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
fn clear_cache() {}

#[pyfunction]
fn set_alignment(_n: i32) {}

#[pyfunction]
fn set_block_size(_n: i32) {}

#[pyfunction]
fn set_blocks_max(_n: i32) {}

#[pyfunction]
fn get_stats() -> (i32, i32) {
    (0, 0)
}

#[pyfunction]
fn reset_stats() {}

#[pyfunction]
#[pyo3(signature = (_image, data, size=None, encoding=None, layout_engine=None))]
fn getfont(
    _image: Py<imaging_core::ImagingCore>,
    data: &[u8],
    size: Option<f32>,
    encoding: Option<&str>,
    layout_engine: Option<i32>,
) -> PyResult<font::Font> {
    let _ = encoding;
    let _ = layout_engine;
    let px_size = size.unwrap_or(12.0);
    let handle = pil_rust_core::font_load(data, px_size)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(font::Font {
        handle,
        size: px_size,
    })
}

#[pyfunction]
#[pyo3(name = "font")]
fn font_load_py(image: Py<imaging_core::ImagingCore>, data: &[u8]) -> PyResult<font::Font> {
    getfont(image, data, None, None, None)
}

#[pymodule]
fn _imaging(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ImagingCore>()?;
    m.add_class::<PixelAccess>()?;
    m.add_class::<ImagingDraw>()?;
    m.add_class::<Font>()?;
    m.add_class::<ImagingPath>()?;
    m.add_class::<ImagingOutline>()?;
    m.add_function(wrap_pyfunction!(draw, m)?)?;
    m.add_function(wrap_pyfunction!(getfont, m)?)?;
    m.add_function(wrap_pyfunction!(font_load_py, m)?)?;
    m.add_function(wrap_pyfunction!(new, m)?)?;
    m.add_function(wrap_pyfunction!(fill, m)?)?;
    m.add_function(wrap_pyfunction!(merge, m)?)?;
    m.add_function(wrap_pyfunction!(blend, m)?)?;
    m.add_function(wrap_pyfunction!(alpha_composite_module, m)?)?;
    m.add_function(wrap_pyfunction!(linear_gradient, m)?)?;
    m.add_function(wrap_pyfunction!(radial_gradient, m)?)?;
    m.add_function(wrap_pyfunction!(open_from_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(gif_save_animated, m)?)?;
    m.add_function(wrap_pyfunction!(gif_decode_frame, m)?)?;
    m.add_function(wrap_pyfunction!(gif_frame_count, m)?)?;
    m.add_function(wrap_pyfunction!(gif_save_with_palette, m)?)?;
    m.add_function(wrap_pyfunction!(save_to_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(path, m)?)?;
    m.add_function(wrap_pyfunction!(new_block, m)?)?;
    m.add_function(wrap_pyfunction!(outline, m)?)?;
    m.add_function(wrap_pyfunction!(effect_mandelbrot, m)?)?;
    m.add_function(wrap_pyfunction!(effect_noise, m)?)?;
    m.add_function(wrap_pyfunction!(clear_cache, m)?)?;
    m.add_function(wrap_pyfunction!(set_alignment, m)?)?;
    m.add_function(wrap_pyfunction!(set_block_size, m)?)?;
    m.add_function(wrap_pyfunction!(set_blocks_max, m)?)?;
    m.add_function(wrap_pyfunction!(get_stats, m)?)?;
    m.add_function(wrap_pyfunction!(reset_stats, m)?)?;

    m.add("PILLOW_VERSION", "12.1.1")?;
    m.add("DEFAULT_STRATEGY", 0i32)?;
    m.add("FILTERED", 1i32)?;
    m.add("HUFFMAN_ONLY", 2i32)?;
    m.add("RLE", 3i32)?;
    m.add("FIXED", 4i32)?;
    m.add("HAVE_LIBIMAGEQUANT", false)?;
    m.add("HAVE_LIBJPEGTURBO", false)?;
    m.add("HAVE_MOZJPEG", false)?;
    m.add("HAVE_XCB", false)?;
    m.add("HAVE_ZLIBNG", false)?;
    m.add("jpeglib_version", "")?;
    m.add("libtiff_version", "")?;
    m.add("zlib_version", "")?;
    m.add("zlib_ng_version", "")?;
    m.add("libjpeg_turbo_version", "")?;
    m.add("jp2klib_version", "")?;

    Ok(())
}
