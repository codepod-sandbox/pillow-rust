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
}
