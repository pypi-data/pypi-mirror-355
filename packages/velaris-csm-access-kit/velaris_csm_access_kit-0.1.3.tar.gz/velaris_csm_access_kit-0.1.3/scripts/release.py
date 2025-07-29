#!/usr/bin/env python3
"""
Release script for velaris-csm-access-kit

This script helps automate the release process by:
1. Creating a new version tag
2. Building the package
3. Optionally publishing to PyPI

Usage:
    python scripts/release.py --version 0.1.1 [--publish]
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def main():
    parser = argparse.ArgumentParser(description="Release velaris-csm-access-kit")
    parser.add_argument("--version", required=True, help="Version to release (e.g., 0.1.1)")
    parser.add_argument("--publish", action="store_true", help="Publish to PyPI after building")
    parser.add_argument("--test-pypi", action="store_true", help="Publish to TestPyPI instead of PyPI")
    
    args = parser.parse_args()
    
    # Validate we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: Must be run from the package root directory")
        sys.exit(1)
    
    version = args.version
    if not version.startswith("v"):
        version = f"v{version}"
    
    print(f"Creating release {version}")
    
    # Check if working directory is clean
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("Error: Working directory is not clean. Commit or stash changes first.")
        sys.exit(1)
    
    # Create and push tag
    run_command(f"git tag {version}")
    run_command(f"git push origin {version}")
    
    # Build package
    print("Building package...")
    run_command("uv build")
    
    if args.publish:
        # Publish to PyPI
        if args.test_pypi:
            print("Publishing to TestPyPI...")
            run_command("uv run twine upload --repository testpypi dist/*")
        else:
            print("Publishing to PyPI...")
            run_command("uv run twine upload dist/*")
    
    print(f"Release {version} completed successfully!")
    if not args.publish:
        print("To publish to PyPI, run:")
        print("  uv run twine upload dist/*")

if __name__ == "__main__":
    main()
