use crate::imaging_core::ImagingCore;
use pyo3::prelude::*;

#[pyclass]
pub struct ImagingDraw {
    pub im: Py<ImagingCore>,
}

/// Unpack a Pillow packed-int color (ARGB u32 stored as i32) or tuple → [r, g, b, a].
fn extract_rgba(color: &Bound<'_, PyAny>) -> PyResult<[u8; 4]> {
    // draw_ink always returns a packed ARGB u32 cast to i32 — reinterpret via u32
    if let Ok(v) = color.extract::<i32>() {
        let uv = v as u32;
        let r = ((uv >> 16) & 0xFF) as u8;
        let g = ((uv >> 8) & 0xFF) as u8;
        let b = (uv & 0xFF) as u8;
        let a = ((uv >> 24) & 0xFF) as u8;
        return Ok([r, g, b, if a == 0 { 255 } else { a }]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8, u8)>() {
        return Ok([t.0, t.1, t.2, t.3]);
    }
    if let Ok(t) = color.extract::<(u8, u8, u8)>() {
        return Ok([t.0, t.1, t.2, 255]);
    }
    if let Ok(v) = color.extract::<u8>() {
        return Ok([v, v, v, 255]);
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "cannot extract color",
    ))
}

/// Accept a bounding box as either:
/// - flat sequence of 4 ints: [x0, y0, x1, y1] or (x0, y0, x1, y1)
/// - list/tuple of 2 (x,y) pairs: [(x0,y0),(x1,y1)]
fn extract_box(xy: &Bound<'_, PyAny>) -> PyResult<(i32, i32, i32, i32)> {
    if let Ok((x0, y0, x1, y1)) = xy.extract::<(i32, i32, i32, i32)>() {
        return Ok((x0, y0, x1, y1));
    }
    if let Ok(pairs) = xy.extract::<Vec<(i32, i32)>>() {
        if pairs.len() >= 2 {
            return Ok((pairs[0].0, pairs[0].1, pairs[1].0, pairs[1].1));
        }
    }
    if let Ok(flat) = xy.extract::<Vec<i32>>() {
        if flat.len() >= 4 {
            return Ok((flat[0], flat[1], flat[2], flat[3]));
        }
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "xy must be a sequence of 4 ints or 2 (x,y) pairs",
    ))
}

/// Validate that x0 <= x1 and y0 <= y1, raising ValueError if not.
fn validate_box_ordered(x0: i32, y0: i32, x1: i32, y1: i32) -> PyResult<()> {
    if x1 < x0 || y1 < y0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "coordinate 'xy' is incorrectly ordered",
        ));
    }
    Ok(())
}

/// Accept coordinates as either flat ints/floats [x0, y0, ...] or list of (x,y) pairs.
fn extract_xy_flat(xy: &Bound<'_, PyAny>) -> PyResult<Vec<i32>> {
    if let Ok(flat) = xy.extract::<Vec<i32>>() {
        return Ok(flat);
    }
    if let Ok(pairs) = xy.extract::<Vec<(i32, i32)>>() {
        let mut result = Vec::with_capacity(pairs.len() * 2);
        for (x, y) in pairs {
            result.push(x);
            result.push(y);
        }
        return Ok(result);
    }
    // Float coordinates (e.g. from regular_polygon)
    if let Ok(flat) = xy.extract::<Vec<f64>>() {
        return Ok(flat.into_iter().map(|v| v.round() as i32).collect());
    }
    if let Ok(pairs) = xy.extract::<Vec<(f64, f64)>>() {
        let mut result = Vec::with_capacity(pairs.len() * 2);
        for (x, y) in pairs {
            result.push(x.round() as i32);
            result.push(y.round() as i32);
        }
        return Ok(result);
    }
    Err(pyo3::exceptions::PyTypeError::new_err(
        "xy must be a flat list of ints or a list of (x,y) pairs",
    ))
}

#[pymethods]
impl ImagingDraw {
    /// draw_rectangle(xy, ink, fill, width=0)
    /// fill=1: fill the rect; fill=0: draw outline only.
    #[pyo3(signature = (box_, ink, fill, width=0))]
    fn draw_rectangle(
        &self,
        box_: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = width;
        let (x0, y0, x1, y1) = extract_box(box_)?;
        validate_box_ordered(x0, y0, x1, y1)?;
        let color = extract_rgba(ink)?;
        let do_fill = fill != 0;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_rectangle(&mut im.handle, x0, y0, x1, y1, color, do_fill);
        Ok(())
    }

    #[pyo3(signature = (xy, ink, width=0))]
    fn draw_line(
        &self,
        xy: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let coords = extract_xy_flat(xy)?;
        if coords.len() < 4 {
            return Ok(());
        }
        let color = extract_rgba(ink)?;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_line(
            &mut im.handle,
            coords[0],
            coords[1],
            coords[2],
            coords[3],
            color,
            width as u32,
        );
        Ok(())
    }

    #[pyo3(signature = (xy, ink, width=0))]
    fn draw_lines(
        &self,
        xy: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let coords = extract_xy_flat(xy)?;
        if coords.len() < 4 {
            return Ok(());
        }
        let color = extract_rgba(ink)?;
        let w = width as u32;
        let mut im = self.im.borrow_mut(py);
        for i in (0..coords.len().saturating_sub(2)).step_by(2) {
            pil_rust_core::draw_line(
                &mut im.handle,
                coords[i],
                coords[i + 1],
                coords[i + 2],
                coords[i + 3],
                color,
                w,
            );
        }
        Ok(())
    }

    /// draw_polygon(xy, ink, fill, width=0, mask=None)
    /// fill=1: fill; fill=0: outline.
    #[pyo3(signature = (xy, ink, fill, width=0, mask=None))]
    fn draw_polygon(
        &self,
        xy: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        width: i32,
        mask: Option<&Bound<'_, PyAny>>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = (width, mask);
        let coords = extract_xy_flat(xy)?;
        let color = extract_rgba(ink)?;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_polygon(&mut im.handle, &coords, color, fill != 0);
        Ok(())
    }

    /// draw_ellipse(xy, ink, fill, width=0)
    /// fill=1: fill; fill=0: outline.
    #[pyo3(signature = (box_, ink, fill, width=0))]
    fn draw_ellipse(
        &self,
        box_: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = width;
        let (x0, y0, x1, y1) = extract_box(box_)?;
        validate_box_ordered(x0, y0, x1, y1)?;
        let color = extract_rgba(ink)?;
        let do_fill = fill != 0;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_ellipse(&mut im.handle, x0, y0, x1, y1, color, do_fill);
        Ok(())
    }

    /// draw_arc(xy, start, end, ink, width=0)
    #[pyo3(signature = (box_, start, end, ink, width=0))]
    fn draw_arc(
        &self,
        box_: &Bound<'_, PyAny>,
        start: f64,
        end: f64,
        ink: &Bound<'_, PyAny>,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = width;
        let (x0, y0, x1, y1) = extract_box(box_)?;
        validate_box_ordered(x0, y0, x1, y1)?;
        let color = extract_rgba(ink)?;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_arc(&mut im.handle, x0, y0, x1, y1, start, end, color);
        Ok(())
    }

    /// draw_chord(xy, start, end, ink, fill, width=0)
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (box_, start, end, ink, fill, width=0))]
    fn draw_chord(
        &self,
        box_: &Bound<'_, PyAny>,
        start: f64,
        end: f64,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = width;
        let (x0, y0, x1, y1) = extract_box(box_)?;
        validate_box_ordered(x0, y0, x1, y1)?;
        let color = extract_rgba(ink)?;
        let do_fill = fill != 0;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_chord(&mut im.handle, x0, y0, x1, y1, start, end, color, do_fill);
        Ok(())
    }

    /// draw_pieslice(xy, start, end, ink, fill, width=0)
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (box_, start, end, ink, fill, width=0))]
    fn draw_pieslice(
        &self,
        box_: &Bound<'_, PyAny>,
        start: f64,
        end: f64,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        width: i32,
        py: Python<'_>,
    ) -> PyResult<()> {
        let _ = width;
        let (x0, y0, x1, y1) = extract_box(box_)?;
        validate_box_ordered(x0, y0, x1, y1)?;
        let color = extract_rgba(ink)?;
        let do_fill = fill != 0;
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_pieslice(&mut im.handle, x0, y0, x1, y1, start, end, color, do_fill);
        Ok(())
    }

    #[pyo3(signature = (xy, ink))]
    fn draw_points(
        &self,
        xy: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let coords = extract_xy_flat(xy)?;
        let color = extract_rgba(ink)?;
        let mut im = self.im.borrow_mut(py);
        let (w, h) = pil_rust_core::size(&im.handle);
        for i in (0..coords.len().saturating_sub(1)).step_by(2) {
            let x = coords[i];
            let y = coords[i + 1];
            if x >= 0 && y >= 0 && x < w as i32 && y < h as i32 {
                pil_rust_core::putpixel(&mut im.handle, x as u32, y as u32, color);
            }
        }
        Ok(())
    }

    fn draw_outline(
        &self,
        _shape: &Bound<'_, PyAny>,
        ink: &Bound<'_, PyAny>,
        fill: i32,
        _py: Python<'_>,
    ) -> PyResult<()> {
        // Stub: _Outline drawing not fully implemented; no-op to avoid errors
        let _ = (ink, fill);
        Ok(())
    }

    fn draw_bitmap(
        &self,
        xy: (i32, i32),
        bitmap: &ImagingCore,
        _ink: Option<&Bound<'_, PyAny>>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::paste(
            &mut im.handle,
            &bitmap.handle,
            xy.0,
            xy.1,
            Some(&bitmap.handle),
        );
        Ok(())
    }

    fn draw_ink(&self, ink: &Bound<'_, PyAny>) -> PyResult<i32> {
        // Pack as ARGB u32, then reinterpret as i32.
        // All callers (draw_lines, draw_rectangle, etc.) reinterpret via extract_rgba.
        let pack = |r: u32, g: u32, b: u32, a: u32| -> i32 {
            ((a << 24) | (r << 16) | (g << 8) | b) as i32
        };
        // Tuple forms take priority so they're checked before int
        if let Ok((r, g, b, a)) = ink.extract::<(i32, i32, i32, i32)>() {
            return Ok(pack(
                r as u32 & 0xFF,
                g as u32 & 0xFF,
                b as u32 & 0xFF,
                a as u32 & 0xFF,
            ));
        }
        if let Ok((r, g, b)) = ink.extract::<(i32, i32, i32)>() {
            return Ok(pack(r as u32 & 0xFF, g as u32 & 0xFF, b as u32 & 0xFF, 255));
        }
        if let Ok((l, a)) = ink.extract::<(i32, i32)>() {
            return Ok(pack(
                l as u32 & 0xFF,
                l as u32 & 0xFF,
                l as u32 & 0xFF,
                a as u32 & 0xFF,
            ));
        }
        if let Ok(v) = ink.extract::<i32>() {
            // Scalar: treat as grayscale (L value or float expanded to all channels)
            let c = (v & 0xFF) as u32;
            return Ok(pack(c, c, c, 255));
        }
        if let Ok(v) = ink.extract::<f64>() {
            let c = v.clamp(0.0, 255.0) as u32;
            return Ok(pack(c, c, c, 255));
        }
        if ink.is_none() {
            return Ok(0);
        }
        Err(pyo3::exceptions::PyTypeError::new_err(
            "draw_ink: unsupported ink type",
        ))
    }
}
