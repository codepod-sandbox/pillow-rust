"""
Test runner for upstream Pillow compatibility tests.

Follows the pattern from numpy-rust/tests/numpy_compat/run_compat.py:
- Vendored upstream test files (minimally adapted)
- xfail.txt for known expected failures
- CI mode (--ci) only fails on unexpected failures

Usage:
    python run_compat.py [--verbose] [--ci]

    Or integrated via the existing test infrastructure — add compat modules
    to tests/python/run_all.py.
"""

import sys
import os
import traceback
import importlib
import importlib.util

# ---------------------------------------------------------------------------
# Setup: make sure PIL and our helper are importable
# ---------------------------------------------------------------------------

_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)

# Add the test directory to sys.path so `from .helper` works via package import
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import our pytest shim if running standalone (not via run_all.py)
if "pytest" not in sys.modules:
    try:
        import pytest_shim
        sys.modules["pytest"] = pytest_shim
    except ImportError:
        # Try from parent tests/python/ directory
        _python_test_dir = os.path.join(_parent_dir, "python")
        if _python_test_dir not in sys.path:
            sys.path.insert(0, _python_test_dir)
        import pytest_shim
        sys.modules["pytest"] = pytest_shim

# Make pillow_compat a proper package so relative imports work
import types as _types
if "pillow_compat" not in sys.modules:
    _pkg = _types.ModuleType("pillow_compat")
    _pkg.__path__ = [_this_dir]
    _pkg.__package__ = "pillow_compat"
    sys.modules["pillow_compat"] = _pkg

# Pre-load our helper as pillow_compat.helper
_helper_path = os.path.join(_this_dir, "helper.py")
if os.path.exists(_helper_path) and "pillow_compat.helper" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "pillow_compat.helper", _helper_path,
        submodule_search_locations=[]
    )
    _helper_mod = importlib.util.module_from_spec(_spec)
    _helper_mod.__package__ = "pillow_compat"
    sys.modules["pillow_compat.helper"] = _helper_mod
    _spec.loader.exec_module(_helper_mod)

# ---------------------------------------------------------------------------
# Load xfail list
# ---------------------------------------------------------------------------

_ci_mode = "--ci" in sys.argv
_verbose = "--verbose" in sys.argv or "-v" in sys.argv

XFAIL_TESTS = set()
_xfail_path = os.path.join(_this_dir, "xfail.txt")
if os.path.exists(_xfail_path):
    with open(_xfail_path) as _xf:
        for _line in _xf:
            _line = _line.strip()
            if _line and not _line.startswith("#"):
                XFAIL_TESTS.add(_line)

# ---------------------------------------------------------------------------
# Discover test modules
# ---------------------------------------------------------------------------

TEST_FILES = [
    "test_imagecolor",
    "test_imagestat",
    "test_imagechops",
    "test_imageenhance",
    "test_imagepath",
    "test_image_tobytes",
    "test_image_copy",
    "test_image_crop",
    "test_image_getbbox",
    "test_image_split",
]

# Only include files that actually exist
AVAILABLE_TESTS = []
for _tf in TEST_FILES:
    _path = os.path.join(_this_dir, _tf + ".py")
    if os.path.exists(_path):
        AVAILABLE_TESTS.append(_tf)


def is_expected_fail(name):
    """Check if a test name matches any xfail pattern."""
    if name in XFAIL_TESTS:
        return True
    # Check prefix matches: "module.test_func" matches "module.test_func[param]"
    for xf in XFAIL_TESTS:
        if name.startswith(xf + "[") or name == xf:
            return True
    return False


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

_SkipTest = type("SkipTest", (Exception,), {})
# Try to get SkipTest from pytest shim
try:
    import pytest as _pt
    if hasattr(_pt, "_SkipTest"):
        _SkipTest = _pt._SkipTest
    elif hasattr(_pt, "SkipException"):
        _SkipTest = _pt.SkipException
except Exception:
    pass


def _expand_parametrize(name, func):
    """Yield (label, callable) for each parametrize combination."""
    parametrize = getattr(func, "_parametrize", None)
    if not parametrize:
        yield name, func
        return

    argnames, argvalues = parametrize
    for i, args in enumerate(argvalues):
        if not isinstance(args, (list, tuple)):
            args = (args,)
        label = "{}[{}]".format(name, i)
        def make_caller(f, a):
            return lambda: f(*a)
        yield label, make_caller(func, args)


class CompatResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.xfailed = 0
        self.xpassed = 0
        self.failures = []

    def run_test(self, full_name, fn, args=()):
        if _verbose:
            sys.stdout.write("  {} ...".format(full_name))
            sys.stdout.flush()

        try:
            fn(*args)
        except _SkipTest:
            self.skipped += 1
            if _verbose:
                print(" SKIP")
            return
        except Exception as e:
            if is_expected_fail(full_name):
                self.xfailed += 1
                if _verbose:
                    print(" XFAIL")
                return
            self.failed += 1
            msg = str(e)[:200]
            self.failures.append((full_name, msg))
            if _verbose:
                print(" FAIL")
            return

        if is_expected_fail(full_name):
            self.xpassed += 1
            if _verbose:
                print(" XPASS")
        self.passed += 1
        if _verbose:
            print(" PASS")

    def run_module(self, mod_name, mod):
        """Run all tests in a loaded module."""
        ns = vars(mod)
        items = []

        # Collect standalone test functions
        for name in sorted(ns):
            obj = ns[name]
            if callable(obj) and name.startswith("test_") and not isinstance(obj, type):
                if getattr(obj, "_skip", False):
                    self.skipped += 1
                    continue
                items.append((mod_name + "." + name, obj))

        # Collect test class methods
        for name in sorted(ns):
            obj = ns[name]
            if isinstance(obj, type) and name.startswith("Test"):
                try:
                    inst = obj()
                except Exception:
                    continue
                for mname in sorted(dir(obj)):
                    if not mname.startswith("test_"):
                        continue
                    method = getattr(inst, mname, None)
                    if method and callable(method):
                        if getattr(method, "_skip", False):
                            self.skipped += 1
                            continue
                        items.append((mod_name + "." + name + "." + mname, method))

        for full_name, func in items:
            for label, caller in _expand_parametrize(full_name, func):
                self.run_test(label, caller)


def load_module(name):
    """Load a compat test module with proper package context."""
    mod_path = os.path.join(_this_dir, name + ".py")
    full_name = "pillow_compat." + name
    spec = importlib.util.spec_from_file_location(
        full_name, mod_path,
        submodule_search_locations=[]
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "pillow_compat"
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_all_compat():
    """Run all compat tests and print summary."""
    results = CompatResults()

    print("pillow_compat: running {} test files ...".format(len(AVAILABLE_TESTS)))

    for tf in AVAILABLE_TESTS:
        print("\n" + "=" * 60)
        print("  " + tf)
        print("=" * 60)
        sys.stdout.flush()

        try:
            mod = load_module(tf)
            results.run_module(tf, mod)
        except _SkipTest as e:
            print("  SKIP (module): {}".format(e))
            results.skipped += 1
        except Exception as e:
            print("  ERROR loading {}: {}".format(tf, e))
            traceback.print_exc()
            results.failed += 1
            results.failures.append((tf, "load error: {}".format(str(e)[:200])))

    # Print summary
    print("\n" + "#" * 60)
    total = results.passed + results.failed + results.skipped + results.xfailed
    if results.failures:
        print("\n--- FAILURES ({}) ---".format(len(results.failures)))
        for fname, fmsg in results.failures:
            print("  FAIL {}: {}".format(fname, fmsg))

    if results.xpassed:
        print("\n  NOTE: {} tests in xfail.txt now pass — consider removing them".format(
            results.xpassed))

    if _ci_mode:
        unexpected = [f for f in results.failures if not is_expected_fail(f[0])]
        print("\npillow_compat (CI): {} passed, {} unexpected failures, "
              "{} xfailed, {} skipped (total {})".format(
                  results.passed, len(unexpected), results.xfailed,
                  results.skipped, total))
        print("#" * 60)
        return len(unexpected) == 0
    else:
        print("\npillow_compat: {} passed, {} failed, {} xfailed, {} skipped "
              "(total {})".format(
                  results.passed, results.failed, results.xfailed,
                  results.skipped, total))
        print("#" * 60)
        return results.failed == 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    success = run_all_compat()
    if not success:
        sys.exit(1)
