use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

/// Stub _Outline class for experimental Pillow outline API compatibility.
/// The actual draw_outline functionality is not fully implemented — this
/// exists so that `Image.core.outline` can be imported without AttributeError.
#[pyclass(name = "_Outline")]
pub struct ImagingOutline {
    pub points: Vec<(f32, f32)>,
}

#[pymethods]
impl ImagingOutline {
    #[new]
    pub fn new() -> Self {
        ImagingOutline {
            points: vec![(0.0, 0.0)],
        }
    }

    fn move_(&mut self, x: f32, y: f32) {
        if let Some(last) = self.points.last_mut() {
            *last = (x, y);
        } else {
            self.points.push((x, y));
        }
    }

    #[pyo3(name = "move")]
    fn move_py(&mut self, x: f32, y: f32) {
        self.move_(x, y);
    }

    fn line(&mut self, x: f32, y: f32) {
        self.points.push((x, y));
    }

    fn curve(&mut self, x1: f32, y1: f32, _x2: f32, _y2: f32, x3: f32, y3: f32) {
        // Approximate cubic bezier with just endpoints for stub
        self.points.push((x1, y1));
        self.points.push((x3, y3));
    }

    fn close(&mut self) {
        if let (Some(&first), Some(&last)) = (self.points.first(), self.points.last()) {
            if first != last {
                self.points.push(first);
            }
        }
    }

    fn transform(&mut self, matrix: (f64, f64, f64, f64, f64, f64)) {
        let (a, b, c, d, e, f) = matrix;
        for (x, y) in &mut self.points {
            let nx = a as f32 * *x + b as f32 * *y + c as f32;
            let ny = d as f32 * *x + e as f32 * *y + f as f32;
            *x = nx;
            *y = ny;
        }
    }
}

#[pyclass]
pub struct ImagingPath {
    pub coords: Vec<(f32, f32)>,
}

#[pymethods]
impl ImagingPath {
    fn __len__(&self) -> usize {
        self.coords.len()
    }

    fn __getitem__(&self, index: &Bound<'_, PyAny>, py: Python<'_>) -> PyResult<Py<PyAny>> {
        use pyo3::types::PySlice;
        let n = self.coords.len() as isize;
        if let Ok(slice) = index.cast::<PySlice>() {
            let indices = slice.indices(n as pyo3::ffi::Py_ssize_t)?;
            let list = pyo3::types::PyList::empty(py);
            let mut i = indices.start;
            while (indices.step > 0 && i < indices.stop) || (indices.step < 0 && i > indices.stop) {
                let (x, y) = self.coords[i as usize];
                list.append((x, y).into_pyobject(py)?)?;
                i += indices.step;
            }
            return Ok(list.into_any().unbind());
        }
        let i = index.extract::<isize>()?;
        let i = if i < 0 { i + n } else { i };
        if i < 0 || i >= n {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "path index out of range",
            ));
        }
        let (x, y) = self.coords[i as usize];
        Ok((x, y).into_pyobject(py)?.into_any().unbind())
    }

    #[pyo3(signature = (flat = None))]
    fn tolist(&self, flat: Option<&Bound<'_, pyo3::PyAny>>, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let is_flat = flat.map(|v| v.is_truthy()).transpose()?.unwrap_or(false);
        if is_flat {
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

    fn compact(&mut self, distance: f32) -> usize {
        if self.coords.is_empty() {
            return 0;
        }
        let original_len = self.coords.len();
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
        original_len - self.coords.len()
    }

    fn map(&mut self, func: &Bound<'_, PyAny>) -> PyResult<()> {
        for (x, y) in &mut self.coords {
            // Try two-argument form first: func(x, y)
            let result_raw = if let Ok(r) = func.call1((*x, *y)) {
                r
            } else {
                // Fall back to tuple form: func((x, y))
                func.call1(((*x, *y),))?
            };
            let result: (f32, f32) = result_raw.extract()?;
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
