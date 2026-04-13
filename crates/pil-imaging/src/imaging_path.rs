use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

#[pyclass]
pub struct ImagingPath {
    pub coords: Vec<(f32, f32)>,
}

#[pymethods]
impl ImagingPath {
    #[pyo3(signature = (flat = None))]
    fn tolist(&self, flat: Option<bool>, py: Python<'_>) -> PyResult<Py<PyAny>> {
        if flat.unwrap_or(false) {
            let flat_vec: Vec<f32> = self.coords.iter().flat_map(|(x, y)| [*x, *y]).collect();
            Ok(flat_vec.into_pyobject(py)?.into_any().unbind())
        } else {
            let list = PyList::empty(py);
            for (x, y) in &self.coords {
                let t = PyTuple::new(py, [*x, *y])?;
                list.append(t)?;
            }
            Ok(list.into_any().unbind())
        }
    }

    fn getbbox(&self) -> Option<(f32, f32, f32, f32)> {
        if self.coords.is_empty() {
            return None;
        }
        let mut x0 = f32::MAX;
        let mut y0 = f32::MAX;
        let mut x1 = f32::MIN;
        let mut y1 = f32::MIN;
        for (x, y) in &self.coords {
            x0 = x0.min(*x);
            y0 = y0.min(*y);
            x1 = x1.max(*x);
            y1 = y1.max(*y);
        }
        Some((x0, y0, x1, y1))
    }

    fn transform(&mut self, matrix: (f32, f32, f32, f32, f32, f32)) {
        let (a, b, c, d, e, f) = matrix;
        for (x, y) in &mut self.coords {
            let nx = a * *x + b * *y + c;
            let ny = d * *x + e * *y + f;
            *x = nx;
            *y = ny;
        }
    }

    fn compact(&mut self, distance: f32) {
        if self.coords.is_empty() {
            return;
        }
        let d2 = distance * distance;
        let mut result = vec![self.coords[0]];
        for &(x, y) in &self.coords[1..] {
            let (lx, ly) = *result.last().unwrap();
            let dx = x - lx;
            let dy = y - ly;
            if dx * dx + dy * dy >= d2 {
                result.push((x, y));
            }
        }
        self.coords = result;
    }

    fn map(&mut self, func: &Bound<'_, PyAny>) -> PyResult<()> {
        for (x, y) in &mut self.coords {
            let result: (f32, f32) = func.call1(((*x, *y),))?.extract()?;
            *x = result.0;
            *y = result.1;
        }
        Ok(())
    }

    #[getter]
    fn id(&self) -> usize {
        self.coords.as_ptr() as usize
    }
}
