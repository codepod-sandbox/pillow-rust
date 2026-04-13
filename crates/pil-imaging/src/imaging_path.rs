use pyo3::prelude::*;

#[pyclass]
#[allow(dead_code)]
pub struct ImagingPath {
    pub coords: Vec<(f32, f32)>,
}
