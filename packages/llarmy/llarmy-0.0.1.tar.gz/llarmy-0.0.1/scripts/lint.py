#!/usr/bin/env python3
"""Linting script for llarmy package."""

import subprocess
import sys
from pathlib import Path


def run_linter(command: list[str], name: str) -> bool:
    """Run a linter and return True if it passes."""
    print(f"🔍 Running {name}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {name} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main() -> None:
    """Run all linting tools."""
    print("🚀 Running linting for llarmy...\n")

    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"

    all_passed = True

    # Run ruff linter
    all_passed &= run_linter(
        [sys.executable, "-m", "ruff", "check", str(src_path)], "Ruff linter"
    )

    # Run mypy
    all_passed &= run_linter(
        [sys.executable, "-m", "mypy", str(src_path)], "MyPy type checker"
    )

    # Run pylint
    all_passed &= run_linter([sys.executable, "-m", "pylint", str(src_path)], "Pylint")

    if all_passed:
        print("\n🎉 All linting checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some linting checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
