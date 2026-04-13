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
        let x0u = x0.max(0) as u32;
        let y0u = y0.max(0) as u32;
        let x1u = (x1 as u32).min(w);
        let y1u = (y1 as u32).min(h);
        let cw = x1u.saturating_sub(x0u);
        let ch = y1u.saturating_sub(y0u);
        let handle = pil_rust_core::crop(&self.handle, x0u, y0u, cw, ch);
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

    #[pyo3(signature = (mask=None, extrema=None))]
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

    #[pyo3(signature = (alpha_only=true))]
    fn getbbox(&self, alpha_only: bool) -> Option<(u32, u32, u32, u32)> {
        let _ = alpha_only;
        pil_rust_core::getbbox(&self.handle)
    }

    fn getextrema(&self) -> Vec<(u8, u8)> {
        pil_rust_core::getextrema(&self.handle)
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

    #[pyo3(signature = (mask=None, extrema=None))]
    fn entropy(&self, mask: Option<&ImagingCore>, extrema: Option<&Bound<'_, PyAny>>) -> f64 {
        let _ = extrema;
        pil_rust_core::entropy(&self.handle, mask.map(|m| &m.handle))
    }

    #[pyo3(signature = (name, args=None))]
    fn filter(&self, name: &str, args: Option<Vec<f32>>) -> PyResult<ImagingCore> {
        let args = args.unwrap_or_default();
        let handle = pil_rust_core::filter(&self.handle, name, &args)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(ImagingCore { handle })
    }

    fn gaussian_blur(&self, radius: f32) -> ImagingCore {
        let handle = pil_rust_core::filter(&self.handle, "gaussian_blur", &[radius])
            .unwrap_or_else(|_| self.handle.clone());
        ImagingCore { handle }
    }

    #[pyo3(signature = (radius, n=None))]
    fn box_blur(&self, radius: f32, n: Option<i32>) -> ImagingCore {
        let _ = n;
        let handle = pil_rust_core::filter(&self.handle, "box_blur", &[radius])
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
        im: &ImagingCore,
        box_: Option<(i32, i32, i32, i32)>,
        mask: Option<&ImagingCore>,
    ) -> PyResult<()> {
        let (x, y) = if let Some((x0, y0, _, _)) = box_ {
            (x0, y0)
        } else {
            (0, 0)
        };
        pil_rust_core::paste(&mut self.handle, &im.handle, x, y, mask.map(|m| &m.handle));
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
    fn putdata(&mut self, data: &[u8], scale: Option<f64>, offset: Option<f64>) {
        let _ = scale;
        let _ = offset;
        pil_rust_core::putdata(&mut self.handle, data);
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
        let data = pil_rust_core::save(&self.handle, "ppm")
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        fp.call_method1("write", (PyBytes::new(fp.py(), &data),))?;
        Ok(())
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

    fn getpalette(&self) -> PyResult<Vec<u8>> {
        Err(pyo3::exceptions::PyValueError::new_err(
            "image has no palette",
        ))
    }

    fn getpalettemode(&self) -> PyResult<String> {
        Err(pyo3::exceptions::PyValueError::new_err(
            "image has no palette",
        ))
    }

    #[pyo3(signature = (data, rawmode=None))]
    fn putpalette(&mut self, data: &Bound<'_, PyAny>, rawmode: Option<&str>) -> PyResult<()> {
        let _ = (data, rawmode);
        Err(pyo3::exceptions::PyValueError::new_err(
            "image has no palette",
        ))
    }

    fn putpalettealpha(&mut self, index: i32, alpha: i32) -> PyResult<()> {
        let _ = (index, alpha);
        Err(pyo3::exceptions::PyValueError::new_err(
            "image has no palette",
        ))
    }

    fn putpalettealphas(&mut self, data: &Bound<'_, PyAny>) -> PyResult<()> {
        let _ = data;
        Err(pyo3::exceptions::PyValueError::new_err(
            "image has no palette",
        ))
    }

    #[pyo3(signature = (size, method, data, filter=None, fill=None, fillcolor=None))]
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
