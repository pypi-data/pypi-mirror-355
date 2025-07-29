#!/usr/bin/env python3
"""Code formatting script for llarmy package."""

import subprocess
import sys
from pathlib import Path


def run_formatter(command: list[str], name: str) -> bool:
    """Run a formatter and return True if it succeeds."""
    print(f"🎨 Running {name}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {name} completed")
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main() -> None:
    """Format all code."""
    print("🚀 Formatting llarmy code...\n")

    # Get project root
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"

    all_passed = True

    # Run ruff formatter (imports sorting, etc.)
    all_passed &= run_formatter(
        [sys.executable, "-m", "ruff", "format", str(src_path)], "Ruff formatter"
    )

    # Run ruff linter with auto-fix
    all_passed &= run_formatter(
        [sys.executable, "-m", "ruff", "check", "--fix", str(src_path)], "Ruff auto-fix"
    )

    # Run black formatter
    all_passed &= run_formatter(
        [sys.executable, "-m", "black", str(src_path)], "Black formatter"
    )

    if all_passed:
        print("\n🎉 Code formatting completed!")
        sys.exit(0)
    else:
        print("\n❌ Some formatting failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
