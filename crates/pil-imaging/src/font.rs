use pil_rust_core::FontHandle;
use pyo3::prelude::*;
use pyo3::PyAny;

#[pyclass]
pub struct Font {
    pub handle: FontHandle,
    pub size: f32,
}

#[pymethods]
impl Font {
    #[getter]
    fn ascent(&self) -> f32 {
        let (ascent, _, _) = pil_rust_core::font_metrics(&self.handle);
        ascent
    }

    #[getter]
    fn descent(&self) -> f32 {
        let (_, descent, _) = pil_rust_core::font_metrics(&self.handle);
        descent
    }

    #[getter]
    fn height(&self) -> f32 {
        let (a, d, _) = pil_rust_core::font_metrics(&self.handle);
        a + d
    }

    #[getter]
    fn x_ppem(&self) -> f32 {
        self.size
    }

    #[getter]
    fn y_ppem(&self) -> f32 {
        self.size
    }

    #[getter]
    fn family(&self) -> &str {
        ""
    }

    #[getter]
    fn style(&self) -> &str {
        ""
    }

    #[getter]
    fn glyphs(&self) -> i32 {
        0
    }

    fn getsize(&self, text: &str) -> (f32, f32) {
        let (x0, y0, x1, y1) = pil_rust_core::font_text_bbox(&self.handle, text, 0.0, 0.0);
        (x1 - x0, y1 - y0)
    }

    fn getlength(&self, text: &str) -> f32 {
        pil_rust_core::font_text_length(&self.handle, text)
    }

    fn getvarnames(&self) -> Vec<String> {
        vec![]
    }

    fn getvaraxes(&self) -> Vec<Py<PyAny>> {
        vec![]
    }

    fn setvarname(&self, _name: &str, _value: f32) -> PyResult<()> {
        Err(pyo3::exceptions::PyNotImplementedError::new_err(
            "variable fonts not supported",
        ))
    }

    fn setvaraxes(&self, _axes: &Bound<'_, PyAny>) -> PyResult<()> {
        Err(pyo3::exceptions::PyNotImplementedError::new_err(
            "variable fonts not supported",
        ))
    }
}
