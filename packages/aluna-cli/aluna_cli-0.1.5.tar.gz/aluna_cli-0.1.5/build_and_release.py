#!/usr/bin/env python3
"""
Build and release script for aluna-cli package.
This script automates the entire build and release process to PyPI.
"""

import subprocess
import sys
import os
from pathlib import Path
import re
from typing import Optional


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result


def get_current_version() -> str:
    """Extract current version from pyproject.toml."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    
    return match.group(1)


def increment_version(version: str, part: str = "patch") -> str:
    """Increment version number."""
    major, minor, patch = map(int, version.split("."))
    
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_version(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    
    with open(pyproject_path, "w") as f:
        f.write(content)
    
    print(f"Updated version to {new_version}")


def main():
    """Main build and release process."""
    # Change to the aluna-cli directory
    os.chdir(Path(__file__).parent)
    
    # Parse arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["major", "minor", "patch"]:
        version_bump = sys.argv[1]
    else:
        version_bump = "patch"
    
    print(f"Starting build and release process (version bump: {version_bump})...")
    
    # 1. Run linting checks
    print("\n1. Running linting checks...")
    result = run_command(["ruff", "check", "src/aluna/"], check=False)
    if result.returncode != 0:
        print("Linting failed! Please fix the issues before releasing.")
        sys.exit(1)
    print("✓ Linting passed")
    
    # 2. Get current version and increment
    current_version = get_current_version()
    new_version = increment_version(current_version, version_bump)
    
    print(f"\n2. Version update: {current_version} → {new_version}")
    response = input("Continue with this version? (y/n): ")
    if response.lower() != "y":
        print("Aborted.")
        sys.exit(0)
    
    update_version(new_version)
    
    # 3. Clean previous build artifacts
    print("\n3. Cleaning previous build artifacts...")
    dist_dir = Path("dist")
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)
        print("✓ Cleaned dist/ directory")
    
    # 4. Build the package
    print("\n4. Building package...")
    run_command(["uv", "build"])
    print("✓ Package built successfully")
    
    # 5. Check the built files
    print("\n5. Checking built files...")
    dist_files = list(dist_dir.glob("*"))
    if len(dist_files) != 2:
        print(f"Expected 2 files in dist/, found {len(dist_files)}")
        sys.exit(1)
    
    for file in dist_files:
        print(f"  - {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    
    # 6. Upload to PyPI
    print("\n6. Uploading to PyPI...")
    response = input("Upload to PyPI? (y/n): ")
    if response.lower() != "y":
        print("Aborted. Package built but not uploaded.")
        sys.exit(0)
    
    run_command(["uv", "run", "twine", "upload", "dist/*"])
    
    print(f"\n✓ Successfully released version {new_version}!")
    print(f"View at: https://pypi.org/project/aluna-cli/{new_version}/")
    print(f"\nUsers can now install with:")
    print(f"  uvx aluna-cli")
    print(f"  pip install aluna-cli=={new_version}")


if __name__ == "__main__":
    main()