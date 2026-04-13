use crate::imaging_core::ImagingCore;
use pyo3::prelude::*;
use pyo3::types::PyTuple;

#[pyclass]
pub struct PixelAccess {
    pub im: Py<ImagingCore>,
    pub readonly: bool,
}

fn extract_rgba(color: &Bound<'_, PyAny>, mode: &str) -> PyResult<[u8; 4]> {
    if let Ok(v) = color.extract::<u8>() {
        return Ok([v, v, v, 255]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8, u8)>() {
        return Ok([t.0, t.1, t.2, t.3]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8)>() {
        return Ok([t.0, t.1, t.2, 255]);
    }
    if let Ok(t) = color.extract::<(u8, u8)>() {
        return Ok([t.0, t.0, t.0, t.1]);
    }
    Err(pyo3::exceptions::PyTypeError::new_err(format!(
        "cannot convert color for mode {mode}"
    )))
}

#[pymethods]
impl PixelAccess {
    fn __getitem__<'py>(&self, py: Python<'py>, xy: (i32, i32)) -> PyResult<Bound<'py, PyAny>> {
        let im = self.im.borrow(py);
        let (w, h) = pil_rust_core::size(&im.handle);
        if xy.0 < 0 || xy.1 < 0 || xy.0 >= w as i32 || xy.1 >= h as i32 {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "pixel index out of range",
            ));
        }
        let px = pil_rust_core::getpixel(&im.handle, xy.0 as u32, xy.1 as u32);
        let mode = pil_rust_core::mode(&im.handle);
        let obj: Bound<'py, PyAny> = match mode {
            "L" => px[0].into_pyobject(py)?.into_any(),
            "LA" => PyTuple::new(py, [px[0], px[3]])?.into_any(),
            "RGB" => PyTuple::new(py, [px[0], px[1], px[2]])?.into_any(),
            "RGBA" => PyTuple::new(py, [px[0], px[1], px[2], px[3]])?.into_any(),
            _ => px[0].into_pyobject(py)?.into_any(),
        };
        Ok(obj)
    }

    fn __setitem__(&self, xy: (i32, i32), color: &Bound<'_, PyAny>) -> PyResult<()> {
        if self.readonly {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "pixel access is read only",
            ));
        }
        let py = color.py();
        let mut im = self.im.borrow_mut(py);
        let (w, h) = pil_rust_core::size(&im.handle);
        if xy.0 < 0 || xy.1 < 0 || xy.0 >= w as i32 || xy.1 >= h as i32 {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "pixel index out of range",
            ));
        }
        let mode = pil_rust_core::mode(&im.handle).to_owned();
        let rgba = extract_rgba(color, &mode)?;
        pil_rust_core::putpixel(&mut im.handle, xy.0 as u32, xy.1 as u32, rgba);
        Ok(())
    }
}
