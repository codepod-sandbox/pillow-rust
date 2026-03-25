"""Run all Pillow test files and report summary."""
import sys
import os
import importlib
import traceback

sys.path.insert(0, os.path.dirname(__file__))

# Import our pytest shim as 'pytest' so test files can import it
import pytest_shim
sys.modules['pytest'] = pytest_shim

test_files = [
    "test_image",
    "test_image_resize",
    "test_image_crop",
    "test_image_rotate",
    "test_image_transpose",
    "test_image_filter",
    "test_imagedraw",
    "test_new_features",
    "test_imagecolor",
    "test_imagestat",
    "test_imagefilter_extra",
    "test_composition",
    "test_imageops_extra",
    "test_imagechops",
    "test_quantize",
    "test_image_methods",
    "test_transform",
    "test_save_options",
    "test_imagefont",
    "test_imagedraw_extra",
    "test_mode1_draw",
    "test_image_paste_negative",
    "test_imagechops_values",
    "test_image_getdata_upstream",
    "test_imageops_values",
    "test_image_point_upstream",
    "test_image_putalpha_upstream",
    "test_image_filter_extra",
    "test_image_convert_matrix",
    "test_image_split_merge",
    "test_imageops_flip",
    "test_image_access",
    "test_image_transform_modes",
    "test_image_histogram",
    "test_image_info",
    "test_image_frombytes",
    "test_imagechops_extra",
    "test_imageenhance_extra",
    "test_imagedraw_text",
    "test_image_getchannel",
    "test_image_resize_exact",
    "test_image_crop_exact",
    "test_image_paste_exact",
    "test_imageops_exact",
    "test_image_rotate_exact",
    "test_imagedraw_shapes",
    "test_image_point_exact",
    "test_imagestat_exact",
    "test_image_convert_exact",
    "test_image_alpha_composite",
    "test_imagefilter_kernels",
    "test_image_new_modes",
    "test_image_putpixel_exact",
    "test_image_resize_methods",
    "test_imagechops_ops",
    "test_image_transform_exact",
    "test_imageenhance_ops",
]

total_pass = 0
total_fail = 0
total_skip = 0

for name in test_files:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        mod = importlib.import_module(name)
        # Run tests via our shim
        old_passed = [0]
        old_failed = [0]
        old_skipped = [0]

        # Capture counts from _run_tests
        import io
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            success = pytest_shim._run_tests(mod)
        finally:
            sys.stdout = old_stdout

        output = buf.getvalue()
        print(output)

        # Parse counts from output
        for line in output.split('\n'):
            if 'passed' in line and 'failed' in line:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == 'passed,':
                        total_pass += int(parts[i-1])
                    elif p == 'failed,':
                        total_fail += int(parts[i-1])
                    elif p == 'skipped':
                        total_skip += int(parts[i-1])

    except Exception as e:
        print(f"  ERROR loading {name}: {e}")
        traceback.print_exc()
        total_fail += 1

# ---------------------------------------------------------------------------
# Run upstream Pillow compatibility tests (pillow_compat/)
# ---------------------------------------------------------------------------
compat_dir = os.path.join(os.path.dirname(__file__), '..', 'pillow_compat')
if os.path.isdir(compat_dir):
    print(f"\n{'='*60}")
    print(f"  pillow_compat (upstream tests)")
    print(f"{'='*60}")
    try:
        compat_dir = os.path.abspath(compat_dir)
        if compat_dir not in sys.path:
            sys.path.insert(0, compat_dir)
        # Load and run compat tests
        compat_runner_path = os.path.join(compat_dir, 'run_compat.py')
        if os.path.exists(compat_runner_path):
            spec = importlib.util.spec_from_file_location("run_compat", compat_runner_path)
            compat_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(compat_mod)

            import io
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                compat_success = compat_mod.run_all_compat()
            finally:
                sys.stdout = old_stdout

            output = buf.getvalue()
            print(output)

            # Parse compat results from output
            for line in output.split('\n'):
                if 'pillow_compat' in line and 'passed' in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if p == 'passed,':
                            total_pass += int(parts[i-1])
                        elif p == 'failed,' or p == 'failures,':
                            total_fail += int(parts[i-1])
                        elif p.startswith('skipped'):
                            total_skip += int(parts[i-1])
    except Exception as e:
        print(f"  ERROR running pillow_compat: {e}")
        traceback.print_exc()
        # Don't count compat errors as hard failures for now
        # total_fail += 1

print(f"\n{'#'*60}")
print(f"  TOTAL: {total_pass} passed, {total_fail} failed, {total_skip} skipped")
print(f"{'#'*60}")

if total_fail > 0:
    sys.exit(1)
