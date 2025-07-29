#!/usr/bin/env python3
"""Build script for llarmy package."""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(command: list[str], description: str) -> None:
    """Run a command and handle errors."""
    print(f"🔨 {description}...")
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
    """Build the package."""
    print("🚀 Building llarmy package...\n")

    # Get project root
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    # Clean previous builds
    if dist_dir.exists():
        print("🧹 Cleaning previous dist...")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print("🧹 Cleaning previous build...")
        shutil.rmtree(build_dir)

    # Run linting first
    print("🔍 Running linting checks...")
    lint_result = subprocess.run([sys.executable, "scripts/lint.py"], cwd=project_root)
    if lint_result.returncode != 0:
        print("❌ Linting failed. Fix issues before building.")
        sys.exit(1)

    # Install build dependencies
    run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "build"],
        "Installing build dependencies",
    )

    # Build the package
    run_command([sys.executable, "-m", "build"], "Building package")

    # List built files
    if dist_dir.exists():
        print("\n📦 Built files:")
        for file in dist_dir.iterdir():
            print(f"   {file.name}")

    print("\n🎉 Package build completed!")
    print("\n📋 Next steps:")
    print("   twine check dist/*          - Check package")
    print("   twine upload --repository testpypi dist/*  - Upload to TestPyPI")
    print("   twine upload dist/*         - Upload to PyPI")


if __name__ == "__main__":
    main()
