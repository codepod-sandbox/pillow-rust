use pil_rust_core::ImageHandle;
use pyo3::prelude::*;

#[pyclass]
#[allow(dead_code)]
pub struct ImagingCore {
    pub handle: ImageHandle,
}
