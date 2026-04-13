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
}
