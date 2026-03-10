use rustpython_vm as vm;

use std::cell::RefCell;
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};

use pil_rust_core::{FontHandle, ImageHandle};

// ---------------------------------------------------------------------------
// Handle management — thread-local map of image and font handles
// ---------------------------------------------------------------------------

static NEXT_ID: AtomicUsize = AtomicUsize::new(1);

thread_local! {
    static IMAGES: RefCell<HashMap<usize, ImageHandle>> = RefCell::new(HashMap::new());
    static FONTS: RefCell<HashMap<usize, FontHandle>> = RefCell::new(HashMap::new());
}

fn alloc_font(handle: FontHandle) -> usize {
    let id = NEXT_ID.fetch_add(1, Ordering::Relaxed);
    FONTS.with(|m| m.borrow_mut().insert(id, handle));
    id
}

fn with_font<F, R>(id: usize, f: F) -> Result<R, String>
where
    F: FnOnce(&FontHandle) -> R,
{
    FONTS.with(|m| {
        let map = m.borrow();
        let h = map
            .get(&id)
            .ok_or_else(|| format!("invalid font handle: {id}"))?;
        Ok(f(h))
    })
}

fn alloc(handle: ImageHandle) -> usize {
    let id = NEXT_ID.fetch_add(1, Ordering::Relaxed);
    IMAGES.with(|m| m.borrow_mut().insert(id, handle));
    id
}

fn with<F, R>(id: usize, f: F) -> Result<R, String>
where
    F: FnOnce(&ImageHandle) -> R,
{
    IMAGES.with(|m| {
        let map = m.borrow();
        let h = map
            .get(&id)
            .ok_or_else(|| format!("invalid image handle: {id}"))?;
        Ok(f(h))
    })
}

fn with_mut<F, R>(id: usize, f: F) -> Result<R, String>
where
    F: FnOnce(&mut ImageHandle) -> R,
{
    IMAGES.with(|m| {
        let mut map = m.borrow_mut();
        let h = map
            .get_mut(&id)
            .ok_or_else(|| format!("invalid image handle: {id}"))?;
        Ok(f(h))
    })
}

// ---------------------------------------------------------------------------
// Public API for interpreter registration
// ---------------------------------------------------------------------------

pub fn pil_module_def(ctx: &vm::Context) -> &'static vm::builtins::PyModuleDef {
    _pil_native::module_def(ctx)
}

// ---------------------------------------------------------------------------
// Native module
// ---------------------------------------------------------------------------

#[vm::pymodule]
pub mod _pil_native {
    use super::*;
    use vm::{PyObjectRef, PyResult, VirtualMachine};

    // -- Image creation / loading -------------------------------------------

    #[pyfunction]
    fn image_open(data: Vec<u8>, vm: &VirtualMachine) -> PyResult<usize> {
        pil_rust_core::open(&data)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_new(
        mode: String,
        width: u32,
        height: u32,
        color: vm::function::OptionalArg<PyObjectRef>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        let color_bytes = match color.into_option() {
            Some(obj) => extract_color(&obj, vm)?,
            None => vec![0],
        };
        pil_rust_core::new_image(&mode, width, height, &color_bytes)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Encode / decode ---------------------------------------------------

    #[pyfunction]
    fn image_save(handle_id: usize, format: String, vm: &VirtualMachine) -> PyResult<Vec<u8>> {
        with(handle_id, |h| pil_rust_core::save(h, &format))
            .map_err(|e| vm.new_value_error(e))?
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_save_with_quality(
        handle_id: usize,
        format: String,
        quality: u8,
        vm: &VirtualMachine,
    ) -> PyResult<Vec<u8>> {
        with(handle_id, |h| {
            pil_rust_core::save_with_options(h, &format, Some(quality))
        })
        .map_err(|e| vm.new_value_error(e))?
        .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Properties --------------------------------------------------------

    #[pyfunction]
    fn image_size(handle_id: usize, vm: &VirtualMachine) -> PyResult<(u32, u32)> {
        with(handle_id, |h| pil_rust_core::size(h)).map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_mode(handle_id: usize, vm: &VirtualMachine) -> PyResult<String> {
        with(handle_id, |h| pil_rust_core::mode(h).to_string()).map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_tobytes(handle_id: usize, vm: &VirtualMachine) -> PyResult<Vec<u8>> {
        with(handle_id, |h| pil_rust_core::tobytes(h)).map_err(|e| vm.new_value_error(e))
    }

    // -- Pixel access ------------------------------------------------------

    #[pyfunction]
    fn image_getpixel(
        handle_id: usize,
        x: u32,
        y: u32,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let rgba = with(handle_id, |h| pil_rust_core::getpixel(h, x, y))
            .map_err(|e| vm.new_value_error(e))?;
        let mode = with(handle_id, |h| pil_rust_core::mode(h).to_string())
            .map_err(|e| vm.new_value_error(e))?;
        // Return tuple matching image mode
        let result: PyObjectRef = match mode.as_str() {
            "L" => vm.ctx.new_int(rgba[0] as i32).into(),
            "LA" => vm::builtins::PyTuple::new_ref(
                vec![
                    vm.ctx.new_int(rgba[0] as i32).into(),
                    vm.ctx.new_int(rgba[3] as i32).into(),
                ],
                &vm.ctx,
            )
            .into(),
            "RGB" => vm::builtins::PyTuple::new_ref(
                vec![
                    vm.ctx.new_int(rgba[0] as i32).into(),
                    vm.ctx.new_int(rgba[1] as i32).into(),
                    vm.ctx.new_int(rgba[2] as i32).into(),
                ],
                &vm.ctx,
            )
            .into(),
            _ => vm::builtins::PyTuple::new_ref(
                vec![
                    vm.ctx.new_int(rgba[0] as i32).into(),
                    vm.ctx.new_int(rgba[1] as i32).into(),
                    vm.ctx.new_int(rgba[2] as i32).into(),
                    vm.ctx.new_int(rgba[3] as i32).into(),
                ],
                &vm.ctx,
            )
            .into(),
        };
        Ok(result)
    }

    #[pyfunction]
    fn image_putpixel(
        handle_id: usize,
        x: u32,
        y: u32,
        color: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| pil_rust_core::putpixel(h, x, y, c))
            .map_err(|e| vm.new_value_error(e))
    }

    // -- Geometric transforms ----------------------------------------------

    #[pyfunction]
    fn image_resize(
        handle_id: usize,
        width: u32,
        height: u32,
        resample: vm::function::OptionalArg<String>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        let filter = resample
            .into_option()
            .unwrap_or_else(|| "bilinear".to_string());
        with(handle_id, |h| {
            pil_rust_core::resize(h, width, height, &filter)
        })
        .map(alloc)
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_crop(handle_id: usize, box_: Vec<u32>, vm: &VirtualMachine) -> PyResult<usize> {
        if box_.len() < 4 {
            return Err(vm.new_value_error("crop box must have 4 values".to_string()));
        }
        let (x, y, x1, y1) = (box_[0], box_[1], box_[2], box_[3]);
        with(handle_id, |h| {
            pil_rust_core::crop(h, x, y, x1.saturating_sub(x), y1.saturating_sub(y))
        })
        .map(alloc)
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_rotate(
        handle_id: usize,
        angle: f32,
        _expand: vm::function::OptionalArg<bool>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::rotate(h, angle))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_convert(handle_id: usize, mode: String, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::convert(h, &mode))
            .map_err(|e| vm.new_value_error(e))?
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_transpose(handle_id: usize, method: u8, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::transpose(h, method))
            .map_err(|e| vm.new_value_error(e))?
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Copy / close ------------------------------------------------------

    #[pyfunction]
    fn image_copy(handle_id: usize, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| h.clone())
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_close(handle_id: usize, _vm: &VirtualMachine) {
        IMAGES.with(|m| m.borrow_mut().remove(&handle_id));
    }

    // -- Filters -----------------------------------------------------------

    #[pyfunction]
    fn image_filter(
        handle_id: usize,
        filter_name: String,
        args: vm::function::OptionalArg<Vec<f32>>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        let filter_args = args.into_option().unwrap_or_default();
        with(handle_id, |h| {
            pil_rust_core::filter(h, &filter_name, &filter_args)
        })
        .map_err(|e| vm.new_value_error(e))?
        .map(alloc)
        .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Drawing -----------------------------------------------------------

    #[pyfunction]
    fn draw_rectangle(
        handle_id: usize,
        xy: Vec<i32>,
        color: PyObjectRef,
        fill: bool,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Err(vm.new_value_error("rectangle xy must have 4 values".to_string()));
        }
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_rectangle(h, xy[0], xy[1], xy[2], xy[3], c, fill)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_line(
        handle_id: usize,
        xy: Vec<i32>,
        color: PyObjectRef,
        width: vm::function::OptionalArg<u32>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Err(vm.new_value_error("line xy must have 4 values".to_string()));
        }
        let c = extract_color_rgba(&color, vm)?;
        let w = width.into_option().unwrap_or(1);
        with_mut(handle_id, |h| {
            pil_rust_core::draw_line(h, xy[0], xy[1], xy[2], xy[3], c, w)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_ellipse(
        handle_id: usize,
        xy: Vec<i32>,
        color: PyObjectRef,
        fill: bool,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Err(vm.new_value_error("ellipse xy must have 4 values".to_string()));
        }
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_ellipse(h, xy[0], xy[1], xy[2], xy[3], c, fill)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_text(
        handle_id: usize,
        x: i32,
        y: i32,
        text: String,
        color: PyObjectRef,
        size: vm::function::OptionalArg<u8>,
        anchor: vm::function::OptionalArg<String>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let c = extract_color_rgba(&color, vm)?;
        let sz = size.into_option().unwrap_or(1);
        let anch = anchor.into_option().unwrap_or_else(|| "left".to_string());
        with_mut(handle_id, |h| {
            pil_rust_core::draw_text(h, x, y, &text, sz, c, &anch)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    // -- Paste -------------------------------------------------------------

    #[pyfunction]
    fn image_paste(
        dst_id: usize,
        src_id: usize,
        x: i32,
        y: i32,
        mask_id: vm::function::OptionalArg<usize>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        // We need both handles simultaneously, so extract clones
        let src = IMAGES.with(|m| {
            m.borrow()
                .get(&src_id)
                .cloned()
                .ok_or_else(|| vm.new_value_error(format!("invalid src handle: {src_id}")))
        })?;
        let mask = match mask_id.into_option() {
            Some(mid) => Some(IMAGES.with(|m| {
                m.borrow()
                    .get(&mid)
                    .cloned()
                    .ok_or_else(|| vm.new_value_error(format!("invalid mask handle: {mid}")))
            })?),
            None => None,
        };
        with_mut(dst_id, |dst| {
            pil_rust_core::paste(dst, &src, x, y, mask.as_ref());
        })
        .map_err(|e| vm.new_value_error(e))
    }

    // -- Channel ops -------------------------------------------------------

    #[pyfunction]
    fn image_split(handle_id: usize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let channels =
            with(handle_id, |h| pil_rust_core::split(h)).map_err(|e| vm.new_value_error(e))?;
        let ids: Vec<PyObjectRef> = channels
            .into_iter()
            .map(|c| vm.ctx.new_int(alloc(c) as i64).into())
            .collect();
        Ok(vm.ctx.new_list(ids).into())
    }

    #[pyfunction]
    fn image_merge(mode: String, channel_ids: Vec<usize>, vm: &VirtualMachine) -> PyResult<usize> {
        // Clone channels out to avoid holding IMAGES borrow while calling alloc
        let cloned: Vec<pil_rust_core::ImageHandle> = IMAGES.with(|m| {
            let map = m.borrow();
            let mut channels = Vec::new();
            for &id in &channel_ids {
                let h = map
                    .get(&id)
                    .ok_or_else(|| vm.new_value_error(format!("invalid channel handle: {id}")))?;
                channels.push(h.clone());
            }
            Ok(channels)
        })?;
        let refs: Vec<&pil_rust_core::ImageHandle> = cloned.iter().collect();
        pil_rust_core::merge(&mode, &refs)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Statistics --------------------------------------------------------

    #[pyfunction]
    fn image_histogram(handle_id: usize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let hist =
            with(handle_id, |h| pil_rust_core::histogram(h)).map_err(|e| vm.new_value_error(e))?;
        let items: Vec<PyObjectRef> = hist
            .into_iter()
            .map(|v| vm.ctx.new_int(v as i64).into())
            .collect();
        Ok(vm.ctx.new_list(items).into())
    }

    #[pyfunction]
    fn image_getbbox(handle_id: usize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let bbox =
            with(handle_id, |h| pil_rust_core::getbbox(h)).map_err(|e| vm.new_value_error(e))?;
        match bbox {
            Some((x0, y0, x1, y1)) => Ok(vm::builtins::PyTuple::new_ref(
                vec![
                    vm.ctx.new_int(x0 as i32).into(),
                    vm.ctx.new_int(y0 as i32).into(),
                    vm.ctx.new_int(x1 as i32).into(),
                    vm.ctx.new_int(y1 as i32).into(),
                ],
                &vm.ctx,
            )
            .into()),
            None => Ok(vm.ctx.none()),
        }
    }

    #[pyfunction]
    fn image_getextrema(handle_id: usize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let extrema =
            with(handle_id, |h| pil_rust_core::getextrema(h)).map_err(|e| vm.new_value_error(e))?;
        if extrema.len() == 1 {
            Ok(vm::builtins::PyTuple::new_ref(
                vec![
                    vm.ctx.new_int(extrema[0].0 as i32).into(),
                    vm.ctx.new_int(extrema[0].1 as i32).into(),
                ],
                &vm.ctx,
            )
            .into())
        } else {
            let tuples: Vec<PyObjectRef> = extrema
                .iter()
                .map(|&(lo, hi)| {
                    vm::builtins::PyTuple::new_ref(
                        vec![
                            vm.ctx.new_int(lo as i32).into(),
                            vm.ctx.new_int(hi as i32).into(),
                        ],
                        &vm.ctx,
                    )
                    .into()
                })
                .collect();
            Ok(vm::builtins::PyTuple::new_ref(tuples, &vm.ctx).into())
        }
    }

    // -- frombytes ---------------------------------------------------------

    #[pyfunction]
    fn image_frombytes(
        mode: String,
        width: u32,
        height: u32,
        data: Vec<u8>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        pil_rust_core::frombytes(&mode, width, height, &data)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Drawing: polygon, arc, pieslice -----------------------------------

    #[pyfunction]
    fn draw_polygon(
        handle_id: usize,
        xy: Vec<i32>,
        color: PyObjectRef,
        fill: bool,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let c = extract_color_rgba(&color, vm)?;
        let points: Vec<(i32, i32)> = xy
            .chunks(2)
            .filter(|c| c.len() == 2)
            .map(|c| (c[0], c[1]))
            .collect();
        with_mut(handle_id, |h| {
            pil_rust_core::draw_polygon(h, &points, c, fill)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_arc(
        handle_id: usize,
        xy: Vec<i32>,
        start: f64,
        end: f64,
        color: PyObjectRef,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Err(vm.new_value_error("arc xy must have 4 values".to_string()));
        }
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_arc(h, xy[0], xy[1], xy[2], xy[3], start, end, c)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_pieslice(
        handle_id: usize,
        xy: Vec<i32>,
        start: f64,
        end: f64,
        color: PyObjectRef,
        fill: bool,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        if xy.len() < 4 {
            return Err(vm.new_value_error("pieslice xy must have 4 values".to_string()));
        }
        let c = extract_color_rgba(&color, vm)?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_pieslice(h, xy[0], xy[1], xy[2], xy[3], start, end, c, fill)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    // -- Enhancement -------------------------------------------------------

    #[pyfunction]
    fn image_adjust_brightness(
        handle_id: usize,
        factor: f32,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::adjust_brightness(h, factor))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_adjust_contrast(
        handle_id: usize,
        factor: f32,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::adjust_contrast(h, factor))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_adjust_color(handle_id: usize, factor: f32, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::adjust_color(h, factor))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_adjust_sharpness(
        handle_id: usize,
        factor: f32,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::adjust_sharpness(h, factor))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    // -- ImageOps ----------------------------------------------------------

    #[pyfunction]
    fn image_autocontrast(handle_id: usize, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::autocontrast(h))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn image_invert(handle_id: usize, vm: &VirtualMachine) -> PyResult<usize> {
        with(handle_id, |h| pil_rust_core::invert_image(h))
            .map(alloc)
            .map_err(|e| vm.new_value_error(e))
    }

    // -- Blend / Composite -------------------------------------------------

    #[pyfunction]
    fn image_blend(id1: usize, id2: usize, alpha: f64, vm: &VirtualMachine) -> PyResult<usize> {
        let (h1, h2) = IMAGES.with(|m| {
            let map = m.borrow();
            let a = map
                .get(&id1)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {id1}")))?
                .clone();
            let b = map
                .get(&id2)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {id2}")))?
                .clone();
            Ok((a, b))
        })?;
        pil_rust_core::blend(&h1, &h2, alpha)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_composite(
        id1: usize,
        id2: usize,
        mask_id: usize,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        let (h1, h2, hm) = IMAGES.with(|m| {
            let map = m.borrow();
            let a = map
                .get(&id1)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {id1}")))?
                .clone();
            let b = map
                .get(&id2)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {id2}")))?
                .clone();
            let mask = map
                .get(&mask_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {mask_id}")))?
                .clone();
            Ok((a, b, mask))
        })?;
        pil_rust_core::composite(&h1, &h2, &hm)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_alpha_composite(dst_id: usize, src_id: usize, vm: &VirtualMachine) -> PyResult<usize> {
        let (dst, src) = IMAGES.with(|m| {
            let map = m.borrow();
            let a = map
                .get(&dst_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {dst_id}")))?
                .clone();
            let b = map
                .get(&src_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {src_id}")))?
                .clone();
            Ok((a, b))
        })?;
        pil_rust_core::alpha_composite(&dst, &src)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Bulk pixel access -------------------------------------------------

    #[pyfunction]
    fn image_getdata(handle_id: usize, vm: &VirtualMachine) -> PyResult<PyObjectRef> {
        let data =
            with(handle_id, |h| pil_rust_core::getdata(h)).map_err(|e| vm.new_value_error(e))?;
        let items: Vec<PyObjectRef> = data
            .into_iter()
            .map(|pixel| {
                if pixel.len() == 1 {
                    vm.ctx.new_int(pixel[0] as i32).into()
                } else {
                    let elems: Vec<PyObjectRef> = pixel
                        .iter()
                        .map(|&v| vm.ctx.new_int(v as i32).into())
                        .collect();
                    vm.ctx.new_tuple(elems).into()
                }
            })
            .collect();
        Ok(vm.ctx.new_list(items).into())
    }

    #[pyfunction]
    fn image_point(handle_id: usize, lut: Vec<u8>, vm: &VirtualMachine) -> PyResult<usize> {
        let handle = IMAGES.with(|m| {
            let map = m.borrow();
            map.get(&handle_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {handle_id}")))
                .cloned()
        })?;
        pil_rust_core::point(&handle, &lut)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    // -- Transform ----------------------------------------------------------

    #[pyfunction]
    fn image_transform_affine(
        handle_id: usize,
        out_w: u32,
        out_h: u32,
        data: Vec<f64>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        if data.len() != 6 {
            return Err(vm.new_value_error("affine transform needs 6 coefficients".to_string()));
        }
        let coeffs: [f64; 6] = [data[0], data[1], data[2], data[3], data[4], data[5]];
        let handle = IMAGES.with(|m| {
            let map = m.borrow();
            map.get(&handle_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {handle_id}")))
                .cloned()
        })?;
        Ok(alloc(pil_rust_core::transform_affine(
            &handle, out_w, out_h, &coeffs,
        )))
    }

    #[pyfunction]
    fn image_transform_perspective(
        handle_id: usize,
        out_w: u32,
        out_h: u32,
        data: Vec<f64>,
        vm: &VirtualMachine,
    ) -> PyResult<usize> {
        if data.len() != 8 {
            return Err(
                vm.new_value_error("perspective transform needs 8 coefficients".to_string())
            );
        }
        let coeffs: [f64; 8] = [
            data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],
        ];
        let handle = IMAGES.with(|m| {
            let map = m.borrow();
            map.get(&handle_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {handle_id}")))
                .cloned()
        })?;
        Ok(alloc(pil_rust_core::transform_perspective(
            &handle, out_w, out_h, &coeffs,
        )))
    }

    // -- Quantize / getcolors -----------------------------------------------

    #[pyfunction]
    fn image_quantize(handle_id: usize, colors: usize, vm: &VirtualMachine) -> PyResult<usize> {
        let handle = IMAGES.with(|m| {
            let map = m.borrow();
            map.get(&handle_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {handle_id}")))
                .cloned()
        })?;
        pil_rust_core::quantize(&handle, colors)
            .map(alloc)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn image_getcolors(
        handle_id: usize,
        maxcolors: usize,
        vm: &VirtualMachine,
    ) -> PyResult<PyObjectRef> {
        let (result, img_mode) = IMAGES.with(|m| {
            let map = m.borrow();
            let h = map
                .get(&handle_id)
                .ok_or_else(|| vm.new_value_error(format!("invalid handle: {handle_id}")))?;
            let mode = pil_rust_core::mode(h);
            Ok((pil_rust_core::getcolors(h, maxcolors), mode.to_string()))
        })?;
        match result {
            None => Ok(vm.ctx.none()),
            Some(colors) => {
                let channels = match img_mode.as_str() {
                    "L" => 1,
                    "LA" => 2,
                    "RGB" => 3,
                    _ => 4,
                };
                let list: Vec<PyObjectRef> = colors
                    .into_iter()
                    .map(|(count, rgba)| {
                        let color: PyObjectRef = match channels {
                            1 => vm.ctx.new_int(rgba[0] as i32).into(),
                            _ => {
                                let vals: Vec<PyObjectRef> = (0..channels)
                                    .map(|i| vm.ctx.new_int(rgba[i] as i32).into())
                                    .collect();
                                vm.ctx.new_tuple(vals).into()
                            }
                        };
                        let pair = vec![vm.ctx.new_int(count as i32).into(), color];
                        vm.ctx.new_tuple(pair).into()
                    })
                    .collect();
                Ok(vm.ctx.new_list(list).into())
            }
        }
    }

    // -- Font functions ----------------------------------------------------

    #[pyfunction]
    fn font_load(data: Vec<u8>, px_size: f32, vm: &VirtualMachine) -> PyResult<usize> {
        pil_rust_core::font_load(&data, px_size)
            .map(alloc_font)
            .map_err(|e| vm.new_value_error(e.to_string()))
    }

    #[pyfunction]
    fn font_load_default(px_size: f32, _vm: &VirtualMachine) -> usize {
        alloc_font(pil_rust_core::font_load_default(px_size))
    }

    #[pyfunction]
    fn font_close(font_id: usize, _vm: &VirtualMachine) {
        FONTS.with(|m| m.borrow_mut().remove(&font_id));
    }

    #[pyfunction]
    fn font_metrics(font_id: usize, vm: &VirtualMachine) -> PyResult<(f32, f32, f32)> {
        with_font(font_id, |fh| pil_rust_core::font_metrics(fh)).map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn font_text_length(font_id: usize, text: String, vm: &VirtualMachine) -> PyResult<f32> {
        with_font(font_id, |fh| pil_rust_core::font_text_length(fh, &text))
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn font_text_bbox(
        font_id: usize,
        text: String,
        x: f32,
        y: f32,
        vm: &VirtualMachine,
    ) -> PyResult<(f32, f32, f32, f32)> {
        with_font(font_id, |fh| pil_rust_core::font_text_bbox(fh, &text, x, y))
            .map_err(|e| vm.new_value_error(e))
    }

    #[pyfunction]
    fn draw_text_ttf(
        handle_id: usize,
        font_id: usize,
        x: f32,
        y: f32,
        text: String,
        color: PyObjectRef,
        anchor: vm::function::OptionalArg<String>,
        vm: &VirtualMachine,
    ) -> PyResult<()> {
        let c = extract_color_rgba(&color, vm)?;
        let anch = anchor.into_option().unwrap_or_else(|| "left".to_string());
        // Clone font to avoid holding FONTS borrow during draw
        let font = FONTS.with(|m| {
            m.borrow()
                .get(&font_id)
                .cloned()
                .ok_or_else(|| vm.new_value_error(format!("invalid font handle: {font_id}")))
        })?;
        with_mut(handle_id, |h| {
            pil_rust_core::draw_text_ttf(h, &font, x, y, &text, c, &anch)
        })
        .map_err(|e| vm.new_value_error(e))
    }

    // -- Helpers -----------------------------------------------------------

    /// Extract a color from a Python object (int, tuple, or list) into bytes.
    fn extract_color(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<Vec<u8>> {
        // Try int first
        if let Ok(v) = obj.try_to_value::<i32>(vm) {
            return Ok(vec![v as u8]);
        }
        // Try tuple/list of ints
        if let Ok(items) = obj.try_to_value::<Vec<i32>>(vm) {
            return Ok(items.into_iter().map(|v| v as u8).collect());
        }
        Err(vm.new_type_error("color must be an int or tuple of ints".to_string()))
    }

    /// Extract a color as [u8; 4] RGBA, padding with defaults.
    fn extract_color_rgba(obj: &PyObjectRef, vm: &VirtualMachine) -> PyResult<[u8; 4]> {
        let bytes = extract_color(obj, vm)?;
        let r = bytes.first().copied().unwrap_or(0);
        let g = bytes.get(1).copied().unwrap_or(0);
        let b = bytes.get(2).copied().unwrap_or(0);
        let a = bytes.get(3).copied().unwrap_or(255);
        Ok([r, g, b, a])
    }
}
