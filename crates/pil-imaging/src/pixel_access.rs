use crate::imaging_core::ImagingCore;
use pyo3::prelude::*;

#[pyclass]
#[allow(dead_code)]
pub struct PixelAccess {
    pub im: Py<ImagingCore>,
    pub readonly: bool,
}
