"""Basic tests for llarmy package."""

from llarmy import __version__
from llarmy.test import add_one


def test_version() -> None:
    """Test that version is available."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_basic_functionality() -> None:
    """Test basic functionality."""
    assert add_one(1) == 2


def test_baseline() -> None:
    """Test basic functionality."""
    assert True
