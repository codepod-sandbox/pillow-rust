"""Minimal pytest shim for running upstream Pillow tests in codepod."""

import sys
import traceback
import re as _re
import builtins as _builtins

# ---------------------------------------------------------------------------
# pytest.raises
# ---------------------------------------------------------------------------

class _RaisesContext:
    def __init__(self, exc_type, match=None):
        self.expected_exception = exc_type
        self.match = match
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"Expected {self.expected_exception.__name__}")
        if not issubclass(exc_type, self.expected_exception):
            return False
        self.value = exc_val
        if self.match and not _re.search(self.match, str(exc_val)):
            raise AssertionError(f"{exc_val!r} did not match {self.match!r}")
        return True

def raises(exc_type, *args, match=None, **kwargs):
    return _RaisesContext(exc_type, match=match)

# ---------------------------------------------------------------------------
# pytest.mark
# ---------------------------------------------------------------------------

class _SkipTest(Exception):
    pass

class _Mark:
    @staticmethod
    def parametrize(argnames, argvalues):
        if isinstance(argnames, str):
            argnames = [a.strip() for a in argnames.split(",")]
        def decorator(func):
            existing = getattr(func, "_parametrize_list", [])
            existing.append((argnames, argvalues))
            func._parametrize_list = existing
            func._parametrize = (argnames, argvalues)
            return func
        return decorator

    @staticmethod
    def skip(reason=""):
        def decorator(func):
            func._skip = reason
            return func
        if callable(reason):
            fn = reason
            fn._skip = ""
            return fn
        return decorator

    @staticmethod
    def skipif(condition, *, reason=""):
        def decorator(func):
            if condition:
                func._skip = reason
            return func
        return decorator

    @staticmethod
    def xfail(reason="", *args, **kwargs):
        def decorator(func):
            func._xfail = reason
            return func
        if callable(reason):
            fn = reason
            fn._xfail = ""
            return fn
        return decorator

mark = _Mark()

# ---------------------------------------------------------------------------
# pytest.fail / pytest.skip / pytest.importorskip
# ---------------------------------------------------------------------------

def fail(msg=""):
    raise AssertionError(msg)

def skip(reason=""):
    raise _SkipTest(reason)

def importorskip(modname, minversion=None, reason=None):
    try:
        mod = __import__(modname)
        return mod
    except ImportError:
        raise _SkipTest(reason or f"could not import {modname!r}")

# ---------------------------------------------------------------------------
# pytest.fixture (minimal)
# ---------------------------------------------------------------------------

def fixture(func=None, *, scope="function", params=None, **kwargs):
    if func is not None:
        func._is_fixture = True
        func._fixture_params = params
        return func
    def decorator(f):
        f._is_fixture = True
        f._fixture_params = params
        return f
    return decorator

# ---------------------------------------------------------------------------
# pytest.approx
# ---------------------------------------------------------------------------

class approx:
    def __init__(self, expected, rel=None, abs=None):
        self.expected = expected
        self.rel = rel
        self.abs_ = abs if abs is not None else 1e-6

    def __eq__(self, other):
        if isinstance(self.expected, (list, tuple)):
            if len(self.expected) != len(other):
                return False
            return all(
                _builtins.abs(a - b) <= self.abs_
                for a, b in zip(self.expected, other)
            )
        return _builtins.abs(self.expected - other) <= self.abs_

    def __repr__(self):
        return f"approx({self.expected})"

# ---------------------------------------------------------------------------
# pytest.warns (stub)
# ---------------------------------------------------------------------------

class _WarnsContext:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False

def warns(*args, **kwargs):
    return _WarnsContext(*args, **kwargs)

# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _expand_parametrize(name, func):
    """Yield (label, callable) for each parametrize combination."""
    parametrize = getattr(func, "_parametrize", None)
    if not parametrize:
        yield name, func
        return

    argnames, argvalues = parametrize
    for args in argvalues:
        if not isinstance(args, (list, tuple)):
            args = (args,)
        label = f"{name}[{'-'.join(str(a) for a in args)}]"
        def make_caller(f, a):
            return lambda: f(*a)
        yield label, make_caller(func, args)


def _run_tests(module):
    passed = 0
    failed = 0
    skipped = 0
    errors = []

    items = sorted(
        [(n, f) for n, f in vars(module).items()
         if n.startswith("test_") and callable(f) and not isinstance(f, type)],
        key=lambda x: x[0]
    )

    classes = [
        (n, c) for n, c in vars(module).items()
        if isinstance(c, type) and n.startswith("Test")
    ]

    for cls_name, cls in sorted(classes, key=lambda x: x[0]):
        try:
            instance = cls()
        except Exception:
            continue
        for method_name in sorted(dir(cls)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name)
            if callable(method):
                items.append((f"{cls_name}.{method_name}", method))

    for name, func in items:
        if hasattr(func, "_skip"):
            skipped += 1
            print(f"  SKIP  {name}: {getattr(func, '_skip', '')}")
            continue

        for label, caller in _expand_parametrize(name, func):
            try:
                caller()
                if hasattr(func, "_xfail"):
                    passed += 1
                    print(f"  XPASS {label}")
                else:
                    passed += 1
                    print(f"  PASS  {label}")
            except _SkipTest as e:
                skipped += 1
                print(f"  SKIP  {label}: {e}")
            except Exception as e:
                if hasattr(func, "_xfail"):
                    skipped += 1
                    print(f"  XFAIL {label}: {e}")
                else:
                    failed += 1
                    errors.append((label, e))
                    print(f"  FAIL  {label}: {e}")

    print(f"\n{'='*50}")
    print(f"  {passed} passed, {failed} failed, {skipped} skipped")
    print(f"{'='*50}")

    if errors:
        print("\nFailure details:")
        for name, err in errors:
            print(f"\n--- {name} ---")
            traceback.print_exception(type(err), err, err.__traceback__)

    return failed == 0

def main(args=None, module=None):
    if module is None:
        module = sys.modules.get("__main__")
    success = _run_tests(module)
    if not success:
        raise SystemExit(1)
