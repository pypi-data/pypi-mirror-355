#!/usr/bin/env python3
"""Test script for llarmy package."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run all tests."""
    print("🚀 Running tests for llarmy...\n")

    # Get project root
    project_root = Path(__file__).parent.parent
    tests_path = project_root / "tests"

    if not tests_path.exists():
        print("📁 Creating tests directory...")
        tests_path.mkdir()
        (tests_path / "__init__.py").touch()
        (
            tests_path / "test_llarmy.py"
        ).write_text('''"""Basic tests for llarmy package."""

import pytest
from llarmy import __version__

def test_version():
    """Test that version is available."""
    assert __version__ is not None
    assert isinstance(__version__, str)

def test_basic_functionality():
    """Test basic functionality."""
    # Add your tests here
    assert True
''')
        print("✅ Basic test file created")

    # Run pytest
    print("🧪 Running pytest...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_path), "-v", "--tb=short"],
            check=True,
            capture_output=True,
            text=True,
        )

        print("✅ All tests passed!")
        if result.stdout:
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        print("❌ Tests failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
