use pil_rust_core::ImageHandle;
use pyo3::prelude::*;

#[pyclass]
pub struct ImagingCore {
    pub handle: ImageHandle,
}

#[pymethods]
impl ImagingCore {
    #[getter]
    fn mode(&self) -> &str {
        pil_rust_core::mode(&self.handle)
    }

    #[getter]
    fn size(&self) -> (u32, u32) {
        pil_rust_core::size(&self.handle)
    }

    #[getter]
    fn bands(&self) -> u32 {
        match pil_rust_core::mode(&self.handle) {
            "L" | "P" => 1,
            "LA" | "PA" => 2,
            "RGB" | "YCbCr" | "LAB" | "HSV" => 3,
            _ => 4,
        }
    }

    #[getter]
    fn readonly(&self) -> bool {
        false
    }

    fn copy(&self) -> ImagingCore {
        ImagingCore {
            handle: self.handle.clone(),
        }
    }

    fn pixel_access(slf: Py<Self>, readonly: bool) -> crate::pixel_access::PixelAccess {
        crate::pixel_access::PixelAccess { im: slf, readonly }
    }

    fn resize(
        &self,
        size: (u32, u32),
        filter: Option<i32>,
        box_: Option<(f64, f64, f64, f64)>,
        reducing_gap: Option<f64>,
    ) -> PyResult<ImagingCore> {
        let _ = box_;
        let _ = reducing_gap;
        let filter_name = match filter.unwrap_or(0) {
            1 => "lanczos",
            2 => "bilinear",
            3 => "bicubic",
            _ => "nearest",
        };
        let handle = pil_rust_core::resize(&self.handle, size.0, size.1, filter_name);
        Ok(ImagingCore { handle })
    }

    fn crop(&self, box_: Option<(i32, i32, i32, i32)>) -> PyResult<ImagingCore> {
        let (w, h) = pil_rust_core::size(&self.handle);
        let (x0, y0, x1, y1) = box_.unwrap_or((0, 0, w as i32, h as i32));
        let x0u = x0.max(0) as u32;
        let y0u = y0.max(0) as u32;
        let x1u = (x1 as u32).min(w);
        let y1u = (y1 as u32).min(h);
        let cw = x1u.saturating_sub(x0u);
        let ch = y1u.saturating_sub(y0u);
        let handle = pil_rust_core::crop(&self.handle, x0u, y0u, cw, ch);
        Ok(ImagingCore { handle })
    }

    fn rotate(
        &self,
        angle: f32,
        resample: Option<i32>,
        expand: Option<bool>,
        center: Option<(f32, f32)>,
        translate: Option<(f32, f32)>,
        fillcolor: Option<i32>,
    ) -> PyResult<ImagingCore> {
        let _ = resample;
        let _ = expand;
        let _ = center;
        let _ = translate;
        let _ = fillcolor;
        let handle = pil_rust_core::rotate(&self.handle, angle);
        Ok(ImagingCore { handle })
    }

    fn transpose(&self, method: i32) -> PyResult<ImagingCore> {
        let handle = pil_rust_core::transpose(&self.handle, method as u8)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn reduce(
        &self,
        factor: &Bound<'_, PyAny>,
        box_: Option<(i32, i32, i32, i32)>,
    ) -> PyResult<ImagingCore> {
        let (fx, fy) = if let Ok(f) = factor.extract::<u32>() {
            (f, f)
        } else if let Ok((fx, fy)) = factor.extract::<(u32, u32)>() {
            (fx, fy)
        } else {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "factor must be int or (int, int)",
            ));
        };
        let src = if let Some((x0, y0, x1, y1)) = box_ {
            let (w, h) = pil_rust_core::size(&self.handle);
            let x0u = x0.max(0) as u32;
            let y0u = y0.max(0) as u32;
            let x1u = (x1 as u32).min(w);
            let y1u = (y1 as u32).min(h);
            pil_rust_core::crop(&self.handle, x0u, y0u, x1u - x0u, y1u - y0u)
        } else {
            self.handle.clone()
        };
        let handle = pil_rust_core::reduce(&src, fx, fy);
        Ok(ImagingCore { handle })
    }

    fn offset(&self, xoffset: i32, yoffset: Option<i32>) -> ImagingCore {
        let yo = yoffset.unwrap_or(xoffset);
        ImagingCore {
            handle: pil_rust_core::offset_image(&self.handle, xoffset, yo),
        }
    }

    fn expand(
        &self,
        x: u32,
        y: Option<u32>,
        color: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<ImagingCore> {
        let y = y.unwrap_or(x);
        let color_bytes: Vec<u8> = if let Some(c) = color {
            if let Ok(v) = c.extract::<u8>() {
                vec![v, v, v, 255]
            } else if let Ok((r, g, b, a)) = c.extract::<(u8, u8, u8, u8)>() {
                vec![r, g, b, a]
            } else if let Ok((r, g, b)) = c.extract::<(u8, u8, u8)>() {
                vec![r, g, b, 255]
            } else {
                vec![0u8; 4]
            }
        } else {
            vec![0u8; 4]
        };
        let handle = pil_rust_core::expand_image(&self.handle, x, y, &color_bytes);
        Ok(ImagingCore { handle })
    }

    fn convert(&self, mode: &str, dither: Option<i32>) -> PyResult<ImagingCore> {
        let _ = dither;
        let handle = pil_rust_core::convert(&self.handle, mode)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn convert2(&self, mode: &str, dither: Option<i32>) -> PyResult<ImagingCore> {
        self.convert(mode, dither)
    }

    fn convert_matrix(&self, mode: &str, matrix: Vec<f32>) -> PyResult<ImagingCore> {
        let handle = pil_rust_core::convert_matrix(&self.handle, mode, &matrix)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn convert_transparent(&self, mode: &str, color: (u8, u8, u8)) -> PyResult<ImagingCore> {
        let _ = mode;
        let mut rgba = pil_rust_core::convert(&self.handle, "RGBA")
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let (w, h) = pil_rust_core::size(&rgba);
        for y in 0..h {
            for x in 0..w {
                let px = pil_rust_core::getpixel(&rgba, x, y);
                if px[0] == color.0 && px[1] == color.1 && px[2] == color.2 {
                    pil_rust_core::putpixel(&mut rgba, x, y, [px[0], px[1], px[2], 0]);
                }
            }
        }
        Ok(ImagingCore { handle: rgba })
    }

    fn setmode(&mut self, mode: &str) -> PyResult<()> {
        let handle = pil_rust_core::convert(&self.handle, mode)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        self.handle = handle;
        Ok(())
    }

    fn point(&self, lut: &Bound<'_, PyAny>, mode: Option<&str>) -> PyResult<ImagingCore> {
        let lut_bytes: Vec<u8> = lut.extract()?;
        let handle = pil_rust_core::point(&self.handle, &lut_bytes)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        if let Some(m) = mode {
            let h2 = pil_rust_core::convert(&handle, m)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            return Ok(ImagingCore { handle: h2 });
        }
        Ok(ImagingCore { handle })
    }

    fn point_transform(&self, scale: Option<f64>, offset: Option<f64>) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::point_transform(
                &self.handle,
                scale.unwrap_or(1.0),
                offset.unwrap_or(0.0),
            ),
        }
    }

    fn split(&self) -> Vec<ImagingCore> {
        pil_rust_core::split(&self.handle)
            .into_iter()
            .map(|h| ImagingCore { handle: h })
            .collect()
    }

    fn getband(&self, n: usize) -> PyResult<ImagingCore> {
        let handle = pil_rust_core::getband(&self.handle, n)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn putband(&self, im: &ImagingCore, n: usize) -> PyResult<ImagingCore> {
        let handle = pil_rust_core::putband(&self.handle, &im.handle, n)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn fillband(&self, n: usize, value: i32) -> PyResult<ImagingCore> {
        let handle = pil_rust_core::fillband(&self.handle, n, value.clamp(0, 255) as u8)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn histogram(
        &self,
        mask: Option<&ImagingCore>,
        extrema: Option<&Bound<'_, PyAny>>,
    ) -> Vec<u32> {
        let _ = extrema;
        match mask {
            Some(m) => pil_rust_core::histogram_masked(&self.handle, &m.handle),
            None => pil_rust_core::histogram(&self.handle),
        }
    }

    fn getbbox(&self) -> Option<(u32, u32, u32, u32)> {
        pil_rust_core::getbbox(&self.handle)
    }

    fn getextrema(&self) -> Vec<(u8, u8)> {
        pil_rust_core::getextrema(&self.handle)
    }

    fn getcolors(&self, maxcolors: Option<usize>, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        use pyo3::types::{PyList, PyTuple};
        let max = maxcolors.unwrap_or(256);
        let colors = pil_rust_core::getcolors(&self.handle, max);
        match colors {
            None => Ok(None),
            Some(entries) => {
                let mode = pil_rust_core::mode(&self.handle);
                let list = PyList::empty(py);
                for (count, px) in entries {
                    let color: Py<PyAny> = match mode {
                        "L" => px[0].into_pyobject(py)?.into_any().unbind(),
                        "LA" => PyTuple::new(py, [px[0], px[3]])?.into_any().unbind(),
                        "RGB" => PyTuple::new(py, [px[0], px[1], px[2]])?.into_any().unbind(),
                        _ => PyTuple::new(py, [px[0], px[1], px[2], px[3]])?
                            .into_any()
                            .unbind(),
                    };
                    let count_obj: Py<PyAny> = count.into_pyobject(py)?.into_any().unbind();
                    let pair = PyTuple::new(py, [count_obj, color])?.into_any().unbind();
                    list.append(pair)?;
                }
                Ok(Some(list.into_any().unbind()))
            }
        }
    }

    fn getprojection(&self) -> (Vec<u32>, Vec<u32>) {
        pil_rust_core::getprojection(&self.handle)
    }

    fn entropy(&self, mask: Option<&ImagingCore>, extrema: Option<&Bound<'_, PyAny>>) -> f64 {
        let _ = extrema;
        pil_rust_core::entropy(&self.handle, mask.map(|m| &m.handle))
    }

    fn transform(
        &self,
        size: (u32, u32),
        method: i32,
        data: &Bound<'_, PyAny>,
        filter: Option<i32>,
        fill: Option<i32>,
        fillcolor: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<ImagingCore> {
        let _ = filter;
        let _ = fill;
        let _ = fillcolor;
        match method {
            0 => {
                // AFFINE: data is 6-element sequence
                let d: Vec<f64> = data.extract()?;
                if d.len() < 6 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "affine needs 6 coefficients",
                    ));
                }
                let coeffs: [f64; 6] = [d[0], d[1], d[2], d[3], d[4], d[5]];
                let handle = pil_rust_core::transform_affine(&self.handle, size.0, size.1, &coeffs);
                Ok(ImagingCore { handle })
            }
            2 => {
                // PERSPECTIVE: data is 8-element sequence
                let d: Vec<f64> = data.extract()?;
                if d.len() < 8 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "perspective needs 8 coefficients",
                    ));
                }
                let coeffs: [f64; 8] = [d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]];
                let handle =
                    pil_rust_core::transform_perspective(&self.handle, size.0, size.1, &coeffs);
                Ok(ImagingCore { handle })
            }
            _ => Err(pyo3::exceptions::PyNotImplementedError::new_err(format!(
                "transform method {method} not implemented"
            ))),
        }
    }
}
