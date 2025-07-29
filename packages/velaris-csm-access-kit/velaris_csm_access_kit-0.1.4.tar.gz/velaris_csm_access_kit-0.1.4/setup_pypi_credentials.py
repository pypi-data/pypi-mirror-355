#!/usr/bin/env python3
"""
Script to help set up PyPI credentials for publishing packages.
"""

import os
from pathlib import Path

def setup_pypirc():
    """Set up .pypirc file with PyPI credentials."""
    
    home_dir = Path.home()
    pypirc_path = home_dir / ".pypirc"
    
    print("Setting up PyPI credentials...")
    print(f"Configuration will be saved to: {pypirc_path}")
    
    # Get API token from user
    print("\nPlease enter your PyPI API token (including the 'pypi-' prefix):")
    print("You can find this at: https://pypi.org/manage/account/token/")
    api_token = input("API Token: ").strip()
    
    if not api_token.startswith("pypi-"):
        print("Warning: API token should start with 'pypi-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return
    
    # Create .pypirc content
    pypirc_content = f"""[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = {api_token}

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = {api_token}
"""
    
    # Write the file
    try:
        with open(pypirc_path, 'w') as f:
            f.write(pypirc_content)
        
        # Set appropriate permissions (readable only by owner)
        os.chmod(pypirc_path, 0o600)
        
        print(f"\n✅ Successfully created {pypirc_path}")
        print("\nYou can now upload to PyPI using:")
        print("  uv run twine upload dist/*")
        print("\nOr to TestPyPI using:")
        print("  uv run twine upload --repository testpypi dist/*")
        
    except Exception as e:
        print(f"❌ Error creating .pypirc file: {e}")

if __name__ == "__main__":
    setup_pypirc()
