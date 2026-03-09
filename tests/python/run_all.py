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

print(f"\n{'#'*60}")
print(f"  TOTAL: {total_pass} passed, {total_fail} failed, {total_skip} skipped")
print(f"{'#'*60}")

if total_fail > 0:
    sys.exit(1)
