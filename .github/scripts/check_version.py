#!/usr/bin/env python3
"""
Check if the version in pyproject.toml has changed compared to the published version on PyPI.

Exit codes:
  0: Version has changed (should publish)
  1: Version has not changed (skip publish)
  2: Error occurred
"""

import sys
import tomli
import requests
from pathlib import Path


def get_local_version():
    """Get version from pyproject.toml"""
    # Try to find pyproject.toml in multiple locations
    script_dir = Path(__file__).parent
    possible_paths = [
        script_dir.parent.parent / "pyproject.toml",  # From .github/scripts/
        Path.cwd() / "pyproject.toml",  # From current directory
        Path(__file__).resolve().parent.parent.parent / "pyproject.toml",  # Absolute path
    ]
    
    pyproject_path = None
    for path in possible_paths:
        if path.exists():
            pyproject_path = path
            break
    
    if pyproject_path is None:
        print("Error: pyproject.toml not found in any expected location", file=sys.stderr)
        print(f"Searched in: {[str(p) for p in possible_paths]}", file=sys.stderr)
        return None
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
            version = data.get("project", {}).get("version")
            if not version:
                print("Error: version not found in pyproject.toml", file=sys.stderr)
                return None
            return version
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}", file=sys.stderr)
        return None


def get_pypi_version(package_name):
    """Get the latest version from PyPI"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            # Package doesn't exist on PyPI yet
            print(f"Package '{package_name}' not found on PyPI (first release)")
            return None
        
        response.raise_for_status()
        data = response.json()
        version = data.get("info", {}).get("version")
        return version
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch PyPI version: {e}", file=sys.stderr)
        return None


def main():
    """Main function"""
    package_name = "commandchat"
    
    # Get local version
    local_version = get_local_version()
    if local_version is None:
        sys.exit(2)
    
    print(f"Local version: {local_version}")
    
    # Get PyPI version
    pypi_version = get_pypi_version(package_name)
    
    if pypi_version is None:
        # First release or PyPI unreachable - allow publish
        print("PyPI version not available. Allowing publish.")
        sys.exit(0)
    
    print(f"PyPI version: {pypi_version}")
    
    # Compare versions
    if local_version == pypi_version:
        print(f"❌ Version {local_version} has not changed. Skipping publish.")
        sys.exit(1)
    else:
        print(f"✅ Version changed from {pypi_version} to {local_version}. Ready to publish.")
        sys.exit(0)


if __name__ == "__main__":
    main()

