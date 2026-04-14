use pil_rust_core::ImageHandle;
use pyo3::prelude::*;

fn extract_palette_bytes(data: &Bound<'_, PyAny>) -> PyResult<Vec<u8>> {
    if let Ok(b) = data.extract::<Vec<u8>>() {
        return Ok(b);
    }
    if let Ok(b) = data.extract::<&[u8]>() {
        return Ok(b.to_vec());
    }
    if let Ok(ints) = data.extract::<Vec<i32>>() {
        return Ok(ints.into_iter().map(|v| v.clamp(0, 255) as u8).collect());
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "putpalette: data must be bytes or list of ints",
    ))
}

/// Extract a scalar f32 from a Python value that is either a float/int or a (x, y) tuple.
/// For tuples, returns the first element (x-radius).
fn extract_scalar_or_first_of_tuple(v: &Bound<'_, PyAny>) -> Option<f32> {
    if let Ok(f) = v.extract::<f32>() {
        return Some(f);
    }
    if let Ok((x, _y)) = v.extract::<(f32, f32)>() {
        return Some(x);
    }
    None
}

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

    fn __len__(&self) -> usize {
        let (w, h) = pil_rust_core::size(&self.handle);
        (w * h) as usize
    }

    fn __getitem__(&self, i: isize, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let (w, h) = pil_rust_core::size(&self.handle);
        let n = (w * h) as isize;
        let i = if i < 0 { i + n } else { i };
        if i < 0 || i >= n {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "index out of range",
            ));
        }
        let x = (i as u32) % w;
        let y = (i as u32) / w;
        let px = pil_rust_core::getpixel(&self.handle, x, y);
        let mode = pil_rust_core::mode(&self.handle);
        let result: Py<PyAny> = match mode {
            "1" => (if px[0] >= 128 { 1i32 } else { 0i32 })
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "L" | "P" => (px[0] as i32).into_pyobject(py)?.into_any().unbind(),
            "LA" | "La" | "PA" => (px[0] as i32, px[3] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "RGB" | "YCbCr" | "LAB" | "HSV" => (px[0] as i32, px[1] as i32, px[2] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "I" | "F" | "I;16" | "I;16B" | "I;16L" | "I;16N" => {
                // 16-bit stored as [lo, hi, 0, 255] — reconstruct the u16 value
                let v = (px[0] as u32) | ((px[1] as u32) << 8);
                (v as i32).into_pyobject(py)?.into_any().unbind()
            }
            _ => (px[0] as i32, px[1] as i32, px[2] as i32, px[3] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
        };
        Ok(result)
    }

    fn copy(&self) -> ImagingCore {
        ImagingCore {
            handle: self.handle.clone(),
        }
    }

    fn pixel_access(
        slf: Py<Self>,
        readonly: &pyo3::Bound<'_, pyo3::PyAny>,
    ) -> PyResult<crate::pixel_access::PixelAccess> {
        let ro = readonly.is_truthy()?;
        Ok(crate::pixel_access::PixelAccess {
            im: slf,
            readonly: ro,
        })
    }

    #[pyo3(signature = (size, filter=None, box_=None, reducing_gap=None))]
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

    fn load(&self) {}

    #[pyo3(signature = (box_=None))]
    fn crop(&self, box_: Option<(i32, i32, i32, i32)>) -> PyResult<ImagingCore> {
        let (w, h) = pil_rust_core::size(&self.handle);
        let (x0, y0, x1, y1) = box_.unwrap_or((0, 0, w as i32, h as i32));
        let handle = pil_rust_core::crop_oob(&self.handle, x0, y0, x1, y1);
        Ok(ImagingCore { handle })
    }

    #[pyo3(signature = (angle, resample=None, expand=None, center=None, translate=None, fillcolor=None))]
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

    #[pyo3(signature = (factor, box_=None))]
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

    #[pyo3(signature = (xoffset, yoffset=None))]
    fn offset(&self, xoffset: i32, yoffset: Option<i32>) -> ImagingCore {
        let yo = yoffset.unwrap_or(xoffset);
        ImagingCore {
            handle: pil_rust_core::offset_image(&self.handle, xoffset, yo),
        }
    }

    #[pyo3(signature = (x, y=None, color=None))]
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

    #[pyo3(signature = (mode, dither=None))]
    fn convert(&self, mode: &str, dither: Option<i32>) -> PyResult<ImagingCore> {
        let _ = dither;
        let handle = pil_rust_core::convert(&self.handle, mode)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    #[pyo3(signature = (mode, dither=None))]
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

    #[pyo3(signature = (lut, mode=None))]
    fn point(&self, lut: &Bound<'_, PyAny>, mode: Option<&str>) -> PyResult<ImagingCore> {
        // LUT values may be out of [0,255] range (e.g. from lambda v: v*2); clamp.
        let lut_bytes: Vec<u8> = if let Ok(v) = lut.extract::<Vec<u8>>() {
            v
        } else if let Ok(v) = lut.extract::<Vec<i64>>() {
            v.iter().map(|&x| x.clamp(0, 255) as u8).collect()
        } else if let Ok(v) = lut.extract::<Vec<f64>>() {
            v.iter().map(|&x| x.clamp(0.0, 255.0) as u8).collect()
        } else {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "lut must be a sequence of numbers",
            ));
        };
        let handle = pil_rust_core::point(&self.handle, &lut_bytes)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        if let Some(m) = mode {
            let h2 = pil_rust_core::convert(&handle, m)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            return Ok(ImagingCore { handle: h2 });
        }
        Ok(ImagingCore { handle })
    }

    #[pyo3(signature = (scale=None, offset=None))]
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

    fn getband(&self, n: i32) -> PyResult<ImagingCore> {
        if n < 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "band index out of range",
            ));
        }
        let handle = pil_rust_core::getband(&self.handle, n as usize)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn putband(&mut self, im: &ImagingCore, n: i32) -> PyResult<()> {
        if n < 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "band index out of range",
            ));
        }
        let handle = pil_rust_core::putband(&self.handle, &im.handle, n as usize)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        self.handle = handle;
        Ok(())
    }

    fn fillband(&mut self, n: usize, value: i32) -> PyResult<()> {
        let handle = pil_rust_core::fillband(&self.handle, n, value.clamp(0, 255) as u8)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        self.handle = handle;
        Ok(())
    }

    /// histogram(extrema=None, mask=None)
    /// Called as: histogram() OR histogram(extrema_tuple) OR histogram(extrema_tuple, mask_im)
    #[pyo3(signature = (extrema=None, mask=None))]
    fn histogram(
        &self,
        extrema: Option<&Bound<'_, PyAny>>,
        mask: Option<&ImagingCore>,
    ) -> Vec<u32> {
        let _ = extrema;
        match mask {
            Some(m) => pil_rust_core::histogram_masked(&self.handle, &m.handle),
            None => pil_rust_core::histogram(&self.handle),
        }
    }

    #[pyo3(signature = (alpha_only=true))]
    fn getbbox(&self, alpha_only: bool) -> Option<(u32, u32, u32, u32)> {
        let _ = alpha_only;
        pil_rust_core::getbbox(&self.handle)
    }

    fn getextrema(&self) -> PyResult<(u8, u8)> {
        let v = pil_rust_core::getextrema(&self.handle);
        v.into_iter()
            .next()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("getextrema: no bands"))
    }

    #[pyo3(signature = (maxcolors=None))]
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
                        "1" => (if px[0] >= 128 { 1u8 } else { 0u8 })
                            .into_pyobject(py)?
                            .into_any()
                            .unbind(),
                        "L" => px[0].into_pyobject(py)?.into_any().unbind(),
                        // getcolors stores LA as [L, A, 0, 0] — use px[1] for alpha
                        "LA" | "La" => PyTuple::new(py, [px[0], px[1]])?.into_any().unbind(),
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

    #[pyo3(signature = (extrema=None, mask=None))]
    fn entropy(&self, extrema: Option<&Bound<'_, PyAny>>, mask: Option<&ImagingCore>) -> f64 {
        let _ = extrema;
        pil_rust_core::entropy(&self.handle, mask.map(|m| &m.handle))
    }

    // Upstream calling convention: im.filter(size_tuple, scale, offset, kernel_seq)
    fn filter(
        &self,
        size: (u32, u32),
        scale: f64,
        offset: f64,
        kernel: Vec<f64>,
    ) -> PyResult<ImagingCore> {
        let (kw, kh) = size;
        let handle = pil_rust_core::apply_kernel(&self.handle, kw, kh, &kernel, scale, offset);
        Ok(ImagingCore { handle })
    }

    fn gaussian_blur(&self, radius: &Bound<'_, PyAny>) -> ImagingCore {
        let r = extract_scalar_or_first_of_tuple(radius).unwrap_or(2.0);
        let handle = pil_rust_core::filter(&self.handle, "gaussian_blur", &[r])
            .unwrap_or_else(|_| self.handle.clone());
        ImagingCore { handle }
    }

    #[pyo3(signature = (radius, n=None))]
    fn box_blur(&self, radius: &Bound<'_, PyAny>, n: Option<i32>) -> ImagingCore {
        let _ = n;
        let r = extract_scalar_or_first_of_tuple(radius).unwrap_or(1.0);
        let handle = pil_rust_core::filter(&self.handle, "box_blur", &[r])
            .unwrap_or_else(|_| self.handle.clone());
        ImagingCore { handle }
    }

    fn unsharp_mask(&self, radius: f32, percent: i32, threshold: i32) -> ImagingCore {
        let handle = pil_rust_core::filter(
            &self.handle,
            "unsharp_mask",
            &[radius, percent as f32, threshold as f32],
        )
        .unwrap_or_else(|_| self.handle.clone());
        ImagingCore { handle }
    }

    fn rankfilter(&self, size: u32, rank: u32) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::rankfilter(&self.handle, size, rank),
        }
    }

    fn modefilter(&self, size: u32) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::modefilter(&self.handle, size),
        }
    }

    #[pyo3(signature = (im, box_=None, mask=None))]
    fn paste(
        &mut self,
        im: &Bound<'_, PyAny>,
        box_: Option<(i32, i32, i32, i32)>,
        mask: Option<&ImagingCore>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let (x, y, x2, y2) = if let Some((x0, y0, x1, y1)) = box_ {
            (x0, y0, x1, y1)
        } else {
            let (w, h) = pil_rust_core::size(&self.handle);
            (0, 0, w as i32, h as i32)
        };

        // Determine if `im` is an ImagingCore or a color value
        if let Ok(src_ref) = im.cast::<ImagingCore>() {
            let src = src_ref.borrow();
            pil_rust_core::paste(&mut self.handle, &src.handle, x, y, mask.map(|m| &m.handle));
        } else {
            // It's a color value — create a temporary image filled with the color
            let mode = pil_rust_core::mode(&self.handle).to_owned();
            let bytes = crate::extract_color_bytes(im, &mode)?;
            let w = (x2 - x).max(0) as u32;
            let h = (y2 - y).max(0) as u32;
            let fill_handle = pil_rust_core::new_image(&mode, w, h, &bytes)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            pil_rust_core::paste(
                &mut self.handle,
                &fill_handle,
                x,
                y,
                mask.map(|m| &m.handle),
            );
        }
        let _ = py;
        Ok(())
    }

    #[pyo3(signature = (im, dest=None, source=None))]
    fn alpha_composite(
        &mut self,
        im: &ImagingCore,
        dest: Option<(i32, i32)>,
        source: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<()> {
        let _ = dest;
        let _ = source;
        let result = pil_rust_core::alpha_composite(&self.handle, &im.handle)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        self.handle = result;
        Ok(())
    }

    fn tobytes(&self) -> Vec<u8> {
        pil_rust_core::tobytes(&self.handle)
    }

    fn getpixel(&self, xy: (i32, i32), py: Python<'_>) -> PyResult<Py<PyAny>> {
        let (mut x, mut y) = xy;
        let (w, h) = pil_rust_core::size(&self.handle);
        // Support negative indices (wrap-around)
        if x < 0 {
            x += w as i32;
        }
        if y < 0 {
            y += h as i32;
        }
        if x < 0 || y < 0 || x >= w as i32 || y >= h as i32 {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "pixel coordinate out of range",
            ));
        }
        let px = pil_rust_core::getpixel(&self.handle, x as u32, y as u32);
        let mode = pil_rust_core::mode(&self.handle);
        let result: Py<PyAny> = match mode {
            "1" => (if px[0] >= 128 { 1i32 } else { 0i32 })
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "L" | "P" => (px[0] as i32).into_pyobject(py)?.into_any().unbind(),
            // image crate's get_pixel converts LumaA→Rgba where A is at index 3
            "LA" | "PA" | "La" => (px[0] as i32, px[3] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "RGB" | "YCbCr" | "LAB" | "HSV" => (px[0] as i32, px[1] as i32, px[2] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "RGBa" | "CMYK" | "RGBX" => (px[0] as i32, px[1] as i32, px[2] as i32, px[3] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
            "I" | "F" | "I;16" | "I;16B" | "I;16L" | "I;16N" => {
                let v = (px[0] as u32) | ((px[1] as u32) << 8);
                (v as i32).into_pyobject(py)?.into_any().unbind()
            }
            _ => (px[0] as i32, px[1] as i32, px[2] as i32, px[3] as i32)
                .into_pyobject(py)?
                .into_any()
                .unbind(),
        };
        Ok(result)
    }

    fn putpixel(&mut self, xy: (i32, i32), color: &Bound<'_, PyAny>) -> PyResult<()> {
        let (mut x, mut y) = xy;
        let (w, h) = pil_rust_core::size(&self.handle);
        // Support negative indices (wrap-around)
        if x < 0 {
            x += w as i32;
        }
        if y < 0 {
            y += h as i32;
        }
        if x < 0 || y < 0 || x >= w as i32 || y >= h as i32 {
            return Err(pyo3::exceptions::PyIndexError::new_err(
                "pixel coordinate out of range",
            ));
        }
        let mode = pil_rust_core::mode(&self.handle).to_owned();
        let bytes = crate::extract_color_bytes(color, &mode)?;
        let rgba = [
            bytes.first().copied().unwrap_or(0),
            bytes.get(1).copied().unwrap_or(0),
            bytes.get(2).copied().unwrap_or(0),
            bytes.get(3).copied().unwrap_or(255),
        ];
        pil_rust_core::putpixel(&mut self.handle, x as u32, y as u32, rgba);
        Ok(())
    }

    fn frombytes(&mut self, data: &[u8]) -> PyResult<()> {
        let (w, h) = pil_rust_core::size(&self.handle);
        let m = pil_rust_core::mode(&self.handle).to_owned();
        self.handle = pil_rust_core::frombytes(&m, w, h, data)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(())
    }

    #[pyo3(signature = (scale=None, offset=None))]
    fn getdata(&self, scale: Option<f64>, offset: Option<f64>) -> Vec<Vec<u8>> {
        let _ = scale;
        let _ = offset;
        pil_rust_core::getdata(&self.handle)
    }

    #[pyo3(signature = (data, scale=None, offset=None))]
    fn putdata(
        &mut self,
        data: &Bound<'_, PyAny>,
        scale: Option<f64>,
        offset: Option<f64>,
    ) -> PyResult<()> {
        let scale = scale.unwrap_or(1.0);
        let offset = offset.unwrap_or(0.0);
        // Pillow uses & 0xFF (wrap-around), applying scale+offset first
        let apply_scale = |v: f64| -> u8 { ((v * scale + offset) as i64 & 0xFF) as u8 };

        let mode = pil_rust_core::mode(&self.handle).to_owned();
        let is_16bit = matches!(
            mode.as_str(),
            "I" | "F" | "I;16" | "I;16L" | "I;16B" | "I;16N"
        );

        // Accept bytes, bytearray, or sequence of ints/floats/tuples.
        // Handle 16-bit modes first to avoid the Vec<u8> branch eating small ints.
        if is_16bit {
            let apply_16 =
                |v: f64| -> u16 { ((v * scale + offset).round() as i64).clamp(0, 0xFFFF) as u16 };
            let bytes: Vec<u8> = if let Ok(seq) = data.extract::<Vec<i64>>() {
                seq.into_iter()
                    .flat_map(|v| apply_16(v as f64).to_le_bytes())
                    .collect()
            } else if let Ok(seq) = data.extract::<Vec<i32>>() {
                seq.into_iter()
                    .flat_map(|v| apply_16(v as f64).to_le_bytes())
                    .collect()
            } else if let Ok(seq) = data.extract::<Vec<f64>>() {
                seq.into_iter()
                    .flat_map(|v| apply_16(v).to_le_bytes())
                    .collect()
            } else {
                return Err(pyo3::exceptions::PyTypeError::new_err(
                    "putdata: unsupported data type for 16-bit mode",
                ));
            };
            pil_rust_core::putdata_16bit(&mut self.handle, &bytes);
        } else if let Ok(bytes) = data.extract::<Vec<u8>>() {
            if scale == 1.0 && offset == 0.0 {
                pil_rust_core::putdata(&mut self.handle, &bytes);
            } else {
                let scaled: Vec<u8> = bytes.into_iter().map(|v| apply_scale(v as f64)).collect();
                pil_rust_core::putdata(&mut self.handle, &scaled);
            }
        } else if let Ok(seq) = data.extract::<Vec<(u8, u8)>>() {
            // 2-tuple modes: LA, Pa — flat bytes [L, A, L, A, ...]
            let bytes: Vec<u8> = seq.into_iter().flat_map(|(a, b)| [a, b]).collect();
            pil_rust_core::putdata(&mut self.handle, &bytes);
        } else if let Ok(seq) = data.extract::<Vec<(u8, u8, u8)>>() {
            let bytes: Vec<u8> = seq.into_iter().flat_map(|(r, g, b)| [r, g, b]).collect();
            pil_rust_core::putdata(&mut self.handle, &bytes);
        } else if let Ok(seq) = data.extract::<Vec<(u8, u8, u8, u8)>>() {
            let bytes: Vec<u8> = seq
                .into_iter()
                .flat_map(|(r, g, b, a)| [r, g, b, a])
                .collect();
            pil_rust_core::putdata(&mut self.handle, &bytes);
        } else if let Ok(seq) = data.extract::<Vec<f64>>() {
            let bytes: Vec<u8> = seq.into_iter().map(apply_scale).collect();
            pil_rust_core::putdata(&mut self.handle, &bytes);
        } else if let Ok(seq) = data.extract::<Vec<i32>>() {
            let bytes: Vec<u8> = seq.into_iter().map(|v| apply_scale(v as f64)).collect();
            pil_rust_core::putdata(&mut self.handle, &bytes);
        } else {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "putdata: unsupported data type",
            ));
        }
        Ok(())
    }

    #[pyo3(signature = (colors, method=None, kmeans=None, palette=None))]
    fn quantize(
        &self,
        colors: usize,
        method: Option<i32>,
        kmeans: Option<i32>,
        palette: Option<&ImagingCore>,
    ) -> PyResult<ImagingCore> {
        let _ = method;
        let _ = kmeans;
        let _ = palette;
        let handle = pil_rust_core::quantize(&self.handle, colors)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn effect_spread(&self, distance: u32) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::effect_spread(&self.handle, distance),
        }
    }

    fn save_ppm(&self, fp: &Bound<'_, PyAny>) -> PyResult<()> {
        use pyo3::types::PyBytes;
        let (w, h) = pil_rust_core::size(&self.handle);
        let mode = pil_rust_core::mode(&self.handle);
        // Build PPM/PGM in memory (simple implementation)
        let is_gray = matches!(mode, "L");
        let magic = if is_gray { "P5" } else { "P6" };
        let mut buf = format!("{}\n{} {}\n255\n", magic, w, h).into_bytes();
        for y in 0..h {
            for x in 0..w {
                let px = pil_rust_core::getpixel(&self.handle, x, y);
                if is_gray {
                    buf.push(px[0]);
                } else {
                    buf.push(px[0]);
                    buf.push(px[1]);
                    buf.push(px[2]);
                }
            }
        }
        // Accept either a filename string or a file-like object
        if let Ok(path) = fp.extract::<String>() {
            std::fs::write(&path, &buf)
                .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
        } else {
            fp.call_method1("write", (PyBytes::new(fp.py(), &buf),))?;
            Ok(())
        }
    }

    #[getter]
    fn ptr(&self) -> usize {
        &self.handle as *const _ as usize
    }

    fn isblock(&self) -> bool {
        false
    }

    #[allow(clippy::too_many_arguments)]
    fn color_lut_3d(
        &self,
        mode: &str,
        filter: i32,
        table_channels: i32,
        size1: i32,
        size2: i32,
        size3: i32,
        table: Vec<f32>,
    ) -> PyResult<ImagingCore> {
        let _ = (mode, filter, table_channels, size1, size2, size3, table);
        Err(pyo3::exceptions::PyNotImplementedError::new_err(
            "color_lut_3d not implemented",
        ))
    }

    #[pyo3(signature = (mode=None, rawmode=None))]
    fn getpalette(&self, mode: Option<&str>, rawmode: Option<&str>) -> PyResult<Vec<u8>> {
        let out_mode = rawmode.or(mode).unwrap_or("RGB");
        pil_rust_core::getpalette(&self.handle, out_mode)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn getpalettemode(&self) -> PyResult<String> {
        pil_rust_core::getpalettemode(&self.handle)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Two calling conventions used by Pillow:
    ///   im.putpalette(palette_mode, rawmode, data)  -- from Image.load()
    ///   im.putpalette(data, rawmode)                -- direct user calls
    /// We detect which by checking whether the first arg is a string or bytes.
    /// rawmode suffix ";L" means planar layout: all R values, then all G, then all B.
    #[pyo3(signature = (arg1, arg2=None, arg3=None))]
    fn putpalette(
        &mut self,
        arg1: &Bound<'_, PyAny>,
        arg2: Option<&Bound<'_, PyAny>>,
        arg3: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<()> {
        let (data_mode, rawmode, bytes) = if let Ok(mode_str) = arg1.extract::<String>() {
            // Called as putpalette(palette_mode, rawmode, data)
            let raw_str = arg2
                .and_then(|a| a.extract::<String>().ok())
                .unwrap_or_else(|| mode_str.clone());
            let data = arg3.or(arg2).ok_or_else(|| {
                pyo3::exceptions::PyTypeError::new_err("putpalette: missing data")
            })?;
            let bytes = extract_palette_bytes(data)?;
            (mode_str, raw_str, bytes)
        } else {
            // Called as putpalette(data, rawmode)
            let bytes = extract_palette_bytes(arg1)?;
            let mode_str = arg2
                .and_then(|a| a.extract::<String>().ok())
                .unwrap_or_else(|| "RGB".to_string());
            (mode_str.clone(), mode_str, bytes)
        };
        // Rawmode ending in ";L" means planar layout: [all-R][all-G][all-B] instead of interleaved.
        // Convert to interleaved before storing.
        let bytes = if rawmode.ends_with(";L") {
            let channels = if data_mode == "RGBA" { 4 } else { 3 };
            let n = bytes.len() / channels;
            let mut interleaved = Vec::with_capacity(bytes.len());
            for i in 0..n {
                for c in 0..channels {
                    interleaved.push(bytes.get(c * n + i).copied().unwrap_or(0));
                }
            }
            interleaved
        } else {
            bytes
        };
        pil_rust_core::putpalette(&mut self.handle, &bytes, &data_mode);
        // Ensure mode_override is P or PA
        if self.handle.mode_override.is_none() || self.handle.mode_override == Some("L") {
            self.handle.mode_override = Some("P");
        }
        Ok(())
    }

    fn putpalettealpha(&mut self, index: i32, alpha: i32) -> PyResult<()> {
        pil_rust_core::putpalettealpha(&mut self.handle, index as usize, alpha.clamp(0, 255) as u8)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn putpalettealphas(&mut self, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let bytes: Vec<u8> = if let Ok(b) = data.extract::<Vec<u8>>() {
            b
        } else if let Ok(ints) = data.extract::<Vec<i32>>() {
            ints.into_iter().map(|v| v.clamp(0, 255) as u8).collect()
        } else {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "putpalettealphas: data must be bytes or list of ints",
            ));
        };
        pil_rust_core::putpalettealphas(&mut self.handle, &bytes)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    // Upstream calling convention: im.transform(box, source_im, method, data, resample, fill)
    // Modifies self in-place, writing the transformed region into `box`.
    #[pyo3(signature = (box_, source, method, data, resample=None, fill=None))]
    fn transform(
        &mut self,
        box_: (i32, i32, i32, i32),
        source: &ImagingCore,
        method: i32,
        data: &Bound<'_, PyAny>,
        resample: Option<i32>,
        fill: Option<bool>,
    ) -> PyResult<()> {
        let _ = resample;
        let _ = fill;
        let (x0, y0, x1, y1) = box_;
        let w = (x1 - x0).max(0) as u32;
        let h = (y1 - y0).max(0) as u32;
        if w == 0 || h == 0 {
            return Ok(());
        }
        let transformed = match method {
            0 => {
                // AFFINE: 6-element inverse transform
                let d: Vec<f64> = data.extract()?;
                if d.len() < 6 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "affine needs 6 coefficients",
                    ));
                }
                pil_rust_core::transform_affine(
                    &source.handle,
                    w,
                    h,
                    &[d[0], d[1], d[2], d[3], d[4], d[5]],
                )
            }
            2 => {
                // PERSPECTIVE: 8-element sequence
                let d: Vec<f64> = data.extract()?;
                if d.len() < 8 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "perspective needs 8 coefficients",
                    ));
                }
                pil_rust_core::transform_perspective(
                    &source.handle,
                    w,
                    h,
                    &[d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]],
                )
            }
            3 => {
                // QUAD: 8-coefficient bilinear transform
                // data = [a0, a1, a2, a3, b0, b1, b2, b3]
                // source_x = a0 + a1*u + a2*v + a3*u*v
                // source_y = b0 + b1*u + b2*v + b3*u*v
                let d: Vec<f64> = data.extract()?;
                if d.len() < 8 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "quad needs 8 coefficients",
                    ));
                }
                pil_rust_core::transform_quad(
                    &source.handle,
                    w,
                    h,
                    &[d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]],
                )
            }
            _ => {
                return Err(pyo3::exceptions::PyNotImplementedError::new_err(format!(
                    "transform method {method} not implemented"
                )));
            }
        };
        // Paste transformed region into self at (x0, y0)
        for dy in 0..h {
            for dx in 0..w {
                let px = pil_rust_core::getpixel(&transformed, dx, dy);
                pil_rust_core::putpixel(
                    &mut self.handle,
                    (x0 + dx as i32) as u32,
                    (y0 + dy as i32) as u32,
                    px,
                );
            }
        }
        Ok(())
    }

    #[pyo3(signature = (im2, scale=None, offset=None))]
    fn chop_add(&self, im2: &ImagingCore, scale: Option<f64>, offset: Option<f64>) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_add(
                &self.handle,
                &im2.handle,
                scale.unwrap_or(1.0),
                offset.unwrap_or(0.0),
            ),
        }
    }
    #[pyo3(signature = (im2, scale=None, offset=None))]
    fn chop_subtract(
        &self,
        im2: &ImagingCore,
        scale: Option<f64>,
        offset: Option<f64>,
    ) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_subtract(
                &self.handle,
                &im2.handle,
                scale.unwrap_or(1.0),
                offset.unwrap_or(0.0),
            ),
        }
    }
    fn chop_add_modulo(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_add_modulo(&self.handle, &im2.handle),
        }
    }
    fn chop_subtract_modulo(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_subtract_modulo(&self.handle, &im2.handle),
        }
    }
    fn chop_multiply(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_multiply(&self.handle, &im2.handle),
        }
    }
    fn chop_screen(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_screen(&self.handle, &im2.handle),
        }
    }
    fn chop_difference(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_difference(&self.handle, &im2.handle),
        }
    }
    fn chop_darker(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_darker(&self.handle, &im2.handle),
        }
    }
    fn chop_lighter(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_lighter(&self.handle, &im2.handle),
        }
    }
    fn chop_invert(&self) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_invert(&self.handle),
        }
    }
    fn chop_and(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_and(&self.handle, &im2.handle),
        }
    }
    fn chop_or(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_or(&self.handle, &im2.handle),
        }
    }
    fn chop_xor(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_xor(&self.handle, &im2.handle),
        }
    }
    fn chop_soft_light(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_soft_light(&self.handle, &im2.handle),
        }
    }
    fn chop_hard_light(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_hard_light(&self.handle, &im2.handle),
        }
    }
    fn chop_overlay(&self, im2: &ImagingCore) -> ImagingCore {
        ImagingCore {
            handle: pil_rust_core::chop_overlay(&self.handle, &im2.handle),
        }
    }
}
