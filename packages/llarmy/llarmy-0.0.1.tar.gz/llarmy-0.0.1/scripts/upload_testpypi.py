#!/usr/bin/env python3
"""Upload script for llarmy package to TestPyPI."""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


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
    """Upload package to TestPyPI."""
    print("🚀 Uploading llarmy to TestPyPI...\n")

    # Load environment variables
    load_env()

    # Check for API key
    api_key = os.getenv("TESTPYPI_API_TOKEN")
    if not api_key:
        print("❌ TESTPYPI_API_TOKEN not found in environment!")
        print("📝 Create a .env file with:")
        print("   TESTPYPI_API_TOKEN=pypi-...")
        print("🔗 Get your token from: https://test.pypi.org/manage/account/token/")
        sys.exit(1)

    # Get project root
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"

    # Check if dist directory exists
    if not dist_dir.exists():
        print("❌ No dist/ directory found!")
        print("🔨 Run 'python scripts/build.py' first")
        sys.exit(1)

    # Check if there are files to upload
    dist_files = list(dist_dir.glob("*"))
    if not dist_files:
        print("❌ No files found in dist/")
        print("🔨 Run 'python scripts/build.py' first")
        sys.exit(1)

    print(f"📦 Found {len(dist_files)} files to upload:")
    for file in dist_files:
        print(f"   {file.name}")

    # Install twine if not available
    print("\n🔧 Ensuring twine is available...")
    run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "twine"],
        "Installing/upgrading twine",
    )

    # Check the package first
    print("\n🔍 Checking package...")
    run_command(
        [sys.executable, "-m", "twine", "check", "dist/*"],
        "Checking package with twine",
    )

    # Upload to TestPyPI
    print("\n🚀 Uploading to TestPyPI...")
    upload_cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--repository",
        "testpypi",
        "--username",
        "__token__",
        "--password",
        api_key,
        "dist/*",
    ]

    try:
        result = subprocess.run(upload_cmd, check=True, capture_output=True, text=True)
        print("✅ Upload successful!")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Upload failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(1)

    print("\n🎉 Package uploaded to TestPyPI!")
    print("🔗 View at: https://test.pypi.org/project/llarmy/")
    print("\n📋 Test installation with:")
    print("   pip install --index-url https://test.pypi.org/simple/ llarmy")


if __name__ == "__main__":
    main()
