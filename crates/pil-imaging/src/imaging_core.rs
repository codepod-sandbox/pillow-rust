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
}
