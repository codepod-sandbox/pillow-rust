"""
conftest.py for upstream Pillow tests.

Upstream tests reference image files relative to the Pillow source root
(e.g. "Tests/images/hopper.png"). We symlink (or alias) those paths so
tests can find the images without modification.
"""
from __future__ import annotations

import os
import pytest

# Register the marks that upstream tests use
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "pil_noop_mark: A conditional mark where nothing special happens",
    )
    config.addinivalue_line(
        "markers",
        "valgrind_known_error: Tests that have known issues with valgrind",
    )
    config.addinivalue_line(
        "markers",
        "timeout: Set a timeout for a test",
    )

    # Make "Tests/images/..." paths work by symlinking Tests/ -> tests/pillow_upstream/
    # in the working directory. We do this by patching os.getcwd-relative resolution:
    # the easiest approach is to cd into a directory that has Tests/ available.


@pytest.fixture(autouse=True)
def chdir_to_upstream(tmp_path, monkeypatch):
    """
    Upstream test files reference images as 'Tests/images/foo.png'.
    Create a symlink Tests/ -> our local images dir so the relative paths work.
    """
    upstream_images = os.path.join(
        os.path.dirname(__file__), "images"
    )
    tests_link = tmp_path / "Tests" / "images"
    tests_link.parent.mkdir(parents=True, exist_ok=True)
    if not tests_link.exists():
        tests_link.symlink_to(upstream_images)
    monkeypatch.chdir(tmp_path)
