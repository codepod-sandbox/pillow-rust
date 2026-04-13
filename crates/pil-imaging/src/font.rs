use pil_rust_core::FontHandle;
use pyo3::prelude::*;

#[pyclass]
#[allow(dead_code)]
pub struct Font {
    pub handle: FontHandle,
    pub size: f32,
}
