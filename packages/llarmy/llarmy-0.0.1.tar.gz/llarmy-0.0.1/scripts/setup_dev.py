#!/usr/bin/env python3
"""Development environment setup script for llarmy package."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list[str], description: str) -> None:
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)


def main() -> None:
    """Set up development environment."""
    print("🚀 Setting up llarmy development environment...\n")

    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Check if we're in a virtual environment
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Not in a virtual environment. Activate with:")
        if os.name == "nt":  # Windows
            print("   .\\venv\\Scripts\\activate")
        else:  # Unix/macOS
            print("   source venv/bin/activate")
        return

    # Upgrade pip
    run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"
    )

    # Install package in editable mode with dev dependencies
    run_command(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
        "Installing package in editable mode with dev dependencies",
    )

    # Install pre-commit hooks
    run_command(
        [sys.executable, "-m", "pre_commit", "install"], "Installing pre-commit hooks"
    )

    print("\n🎉 Development environment setup complete!")
    print("\n📋 Available development commands:")
    print("   python scripts/lint.py       - Run linting")
    print("   python scripts/test.py       - Run tests")
    print("   python scripts/format.py     - Format code")
    print("   python scripts/build.py      - Build package")


if __name__ == "__main__":
    main()
