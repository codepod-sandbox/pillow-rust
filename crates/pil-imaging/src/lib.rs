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

pub fn extract_color_bytes(color: &Bound<'_, PyAny>, _mode: &str) -> PyResult<Vec<u8>> {
    if let Ok(v) = color.extract::<u8>() {
        return Ok(vec![v, v, v, 255]);
    }
    if let Ok(v) = color.extract::<f64>() {
        let b = v.clamp(0.0, 255.0) as u8;
        return Ok(vec![b, b, b, 255]);
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
            return Ok(vec![b, b, b, 255]);
        }
    }
    if let Ok(v) = color.extract::<i32>() {
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
fn linear_gradient(_mode: &str) -> imaging_core::ImagingCore {
    imaging_core::ImagingCore {
        handle: pil_rust_core::linear_gradient(),
    }
}

#[pyfunction]
fn radial_gradient(_mode: &str) -> imaging_core::ImagingCore {
    imaging_core::ImagingCore {
        handle: pil_rust_core::radial_gradient(),
    }
}

#[pyfunction]
fn open_from_bytes(data: &[u8]) -> PyResult<imaging_core::ImagingCore> {
    let handle = pil_rust_core::open(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
#[pyo3(signature = (im, format, **_kwargs))]
fn save_to_bytes<'py>(
    im: &imaging_core::ImagingCore,
    format: &str,
    _kwargs: Option<&Bound<'py, pyo3::types::PyDict>>,
    py: Python<'py>,
) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
    let data = pil_rust_core::save(&im.handle, &format.to_ascii_lowercase())
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &data))
}

#[pyfunction]
#[pyo3(signature = (coords=None))]
fn path(coords: Option<&Bound<'_, PyAny>>) -> PyResult<imaging_path::ImagingPath> {
    let Some(coords) = coords else {
        return Ok(imaging_path::ImagingPath { coords: vec![] });
    };
    let pts: Vec<(f32, f32)> = if let Ok(flat) = coords.extract::<Vec<f32>>() {
        if flat.len() % 2 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "incorrect number of coordinates",
            ));
        }
        flat.chunks(2).map(|c| (c[0], c[1])).collect()
    } else if let Ok(pairs) = coords.extract::<Vec<(f32, f32)>>() {
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
#[pyo3(signature = (size, _xy, _color))]
fn effect_mandelbrot(
    size: &Bound<'_, PyAny>,
    _xy: &Bound<'_, PyAny>,
    _color: i32,
) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    let handle = pil_rust_core::new_image("RGB", w, h, &[0, 0, 0, 255])
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(imaging_core::ImagingCore { handle })
}

#[pyfunction]
#[pyo3(signature = (size, _seed))]
fn effect_noise(size: &Bound<'_, PyAny>, _seed: i32) -> PyResult<imaging_core::ImagingCore> {
    let (w, h) = extract_size(size)?;
    let handle = pil_rust_core::new_image("L", w, h, &[128, 128, 128, 255])
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
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
