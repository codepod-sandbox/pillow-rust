use crate::imaging_core::ImagingCore;
use pyo3::prelude::*;

#[pyclass]
pub struct ImagingDraw {
    pub im: Py<ImagingCore>,
}

fn extract_rgba(color: &Bound<'_, PyAny>) -> PyResult<[u8; 4]> {
    // Pillow may pass color as packed i32 (ABGR or ARGB encoding) or as tuple
    if let Ok(v) = color.extract::<i32>() {
        // Pillow encodes as packed int: low byte = B, next = G, next = R, high = A
        let r = ((v >> 16) & 0xFF) as u8;
        let g = ((v >> 8) & 0xFF) as u8;
        let b = (v & 0xFF) as u8;
        let a = ((v >> 24) & 0xFF) as u8;
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

#[pymethods]
impl ImagingDraw {
    fn draw_rectangle(
        &self,
        box_: (i32, i32, i32, i32),
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_color_arg) = fill {
            let fill_color = extract_rgba(fill_color_arg)?;
            pil_rust_core::draw_rectangle(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                fill_color,
                true,
            );
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            let do_fill = fill.is_none() && width.unwrap_or(0) == 0;
            if width.unwrap_or(0) > 0 || fill.is_none() {
                pil_rust_core::draw_rectangle(
                    &mut im.handle,
                    box_.0,
                    box_.1,
                    box_.2,
                    box_.3,
                    color,
                    do_fill,
                );
            }
        }
        Ok(())
    }

    fn draw_line(
        &self,
        xy: Vec<i32>,
        ink: Option<&Bound<'_, PyAny>>,
        width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Ok(());
        }
        let color = ink
            .map(|c| extract_rgba(c))
            .transpose()?
            .unwrap_or([0u8; 4]);
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_line(
            &mut im.handle,
            xy[0],
            xy[1],
            xy[2],
            xy[3],
            color,
            width.unwrap_or(0) as u32,
        );
        Ok(())
    }

    fn draw_lines(
        &self,
        xy: Vec<i32>,
        ink: Option<&Bound<'_, PyAny>>,
        width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Ok(());
        }
        let color = ink
            .map(|c| extract_rgba(c))
            .transpose()?
            .unwrap_or([0u8; 4]);
        let w = width.unwrap_or(0) as u32;
        let mut im = self.im.borrow_mut(py);
        for i in (0..xy.len().saturating_sub(2)).step_by(2) {
            pil_rust_core::draw_line(
                &mut im.handle,
                xy[i],
                xy[i + 1],
                xy[i + 2],
                xy[i + 3],
                color,
                w,
            );
        }
        Ok(())
    }

    fn draw_polygon(
        &self,
        xy: Vec<i32>,
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_arg) = fill {
            let fill_color = extract_rgba(fill_arg)?;
            pil_rust_core::draw_polygon(&mut im.handle, &xy, fill_color, true);
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            pil_rust_core::draw_polygon(&mut im.handle, &xy, color, false);
        }
        Ok(())
    }

    fn draw_ellipse(
        &self,
        box_: (i32, i32, i32, i32),
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        _width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_arg) = fill {
            let fill_color = extract_rgba(fill_arg)?;
            pil_rust_core::draw_ellipse(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                fill_color,
                true,
            );
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            pil_rust_core::draw_ellipse(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                color,
                false,
            );
        }
        Ok(())
    }

    fn draw_arc(
        &self,
        box_: (i32, i32, i32, i32),
        start: f64,
        end: f64,
        ink: Option<&Bound<'_, PyAny>>,
        _width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let color = ink
            .map(|c| extract_rgba(c))
            .transpose()?
            .unwrap_or([0u8; 4]);
        let mut im = self.im.borrow_mut(py);
        pil_rust_core::draw_arc(
            &mut im.handle,
            box_.0,
            box_.1,
            box_.2,
            box_.3,
            start,
            end,
            color,
        );
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn draw_chord(
        &self,
        box_: (i32, i32, i32, i32),
        start: f64,
        end: f64,
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        _width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_arg) = fill {
            let fill_color = extract_rgba(fill_arg)?;
            pil_rust_core::draw_chord(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                start,
                end,
                fill_color,
                true,
            );
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            pil_rust_core::draw_chord(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                start,
                end,
                color,
                false,
            );
        }
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn draw_pieslice(
        &self,
        box_: (i32, i32, i32, i32),
        start: f64,
        end: f64,
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        _width: Option<i32>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_arg) = fill {
            let fill_color = extract_rgba(fill_arg)?;
            pil_rust_core::draw_pieslice(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                start,
                end,
                fill_color,
                true,
            );
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            pil_rust_core::draw_pieslice(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                start,
                end,
                color,
                false,
            );
        }
        Ok(())
    }

    fn draw_points(
        &self,
        xy: Vec<i32>,
        ink: Option<&Bound<'_, PyAny>>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let color = ink
            .map(|c| extract_rgba(c))
            .transpose()?
            .unwrap_or([0u8; 4]);
        let mut im = self.im.borrow_mut(py);
        let (w, h) = pil_rust_core::size(&im.handle);
        for i in (0..xy.len().saturating_sub(1)).step_by(2) {
            let x = xy[i];
            let y = xy[i + 1];
            if x >= 0 && y >= 0 && x < w as i32 && y < h as i32 {
                pil_rust_core::putpixel(&mut im.handle, x as u32, y as u32, color);
            }
        }
        Ok(())
    }

    fn draw_outline(
        &self,
        box_: (i32, i32, i32, i32),
        ink: Option<&Bound<'_, PyAny>>,
        fill: Option<&Bound<'_, PyAny>>,
        py: Python<'_>,
    ) -> PyResult<()> {
        let mut im = self.im.borrow_mut(py);
        if let Some(fill_arg) = fill {
            let fill_color = extract_rgba(fill_arg)?;
            pil_rust_core::draw_rectangle(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                fill_color,
                true,
            );
        }
        if let Some(ink_arg) = ink {
            let color = extract_rgba(ink_arg)?;
            pil_rust_core::draw_rectangle(
                &mut im.handle,
                box_.0,
                box_.1,
                box_.2,
                box_.3,
                color,
                false,
            );
        }
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

    fn draw_ink(&self, ink: i32) -> i32 {
        ink
    }
}
