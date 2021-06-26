"""Tests for searents/__init__.py"""

import pytest

import searents


@pytest.mark.xfail
def test_version():
    """Ensure searents.__version__ is defined."""
    assert hasattr(searents, "__version__")
    assert isinstance(searents.__version__, str)
