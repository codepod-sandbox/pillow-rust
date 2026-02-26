use rustpython_vm as vm;

use std::cell::RefCell;
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};

use pil_rust_core::ImageHandle;

// ---------------------------------------------------------------------------
// Handle management — thread-local map of image handles
// ---------------------------------------------------------------------------

static NEXT_ID: AtomicUsize = AtomicUsize::new(1);

thread_local! {
    static IMAGES: RefCell<HashMap<usize, ImageHandle>> = RefCell::new(HashMap::new());
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
        let mode =
            with(handle_id, |h| pil_rust_core::mode(h).to_string())
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
        with(handle_id, |h| pil_rust_core::resize(h, width, height, &filter))
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
        xy: Vec<u32>,
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
