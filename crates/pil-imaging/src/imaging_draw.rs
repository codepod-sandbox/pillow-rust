use crate::imaging_core::ImagingCore;
use pyo3::prelude::*;

#[pyclass]
#[allow(dead_code)]
pub struct ImagingDraw {
    pub im: Py<ImagingCore>,
}
