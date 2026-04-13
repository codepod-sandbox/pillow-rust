use pyo3::prelude::*;

mod font;
mod imaging_core;
mod imaging_draw;
mod imaging_path;
mod pixel_access;

use font::Font;
use imaging_core::ImagingCore;
use imaging_draw::ImagingDraw;
use imaging_path::ImagingPath;
use pixel_access::PixelAccess;

#[pyfunction]
fn draw(im: Py<imaging_core::ImagingCore>) -> imaging_draw::ImagingDraw {
    imaging_draw::ImagingDraw { im }
}

#[pyfunction]
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
    m.add_function(wrap_pyfunction!(draw, m)?)?;
    m.add_function(wrap_pyfunction!(getfont, m)?)?;
    m.add_function(wrap_pyfunction!(font_load_py, m)?)?;

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
