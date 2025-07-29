#!/usr/bin/env python3
"""
Release script for MCP Documentation Server.
Handles building, testing, and publishing the package.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import shutil

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error in {description}:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    print(f"Success: {description}")
    if result.stdout:
        print(f"Output: {result.stdout}")
    return True

def clean_build():
    """Clean build directories."""
    print("Cleaning build directories...")
    
    for dir_name in ["build", "dist", "*.egg-info"]:
        for path in Path(".").glob(dir_name):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed: {path}")
    
    print("Build directories cleaned.")

def run_tests():
    """Run test suite."""
    print("Running tests...")
    
    # Check if test files exist
    test_files = list(Path(".").glob("test*.py"))
    if not test_files:
        print("No test files found. Skipping tests.")
        return True
    
    return run_command([sys.executable, "-m", "pytest", "-v"], "Running tests")

def build_package():
    """Build the package."""
    print("Building package...")
    
    # Install build requirements
    if not run_command([sys.executable, "-m", "pip", "install", "build", "twine"], 
                      "Installing build requirements"):
        return False
    
    # Build the package
    if not run_command([sys.executable, "-m", "build"], "Building package"):
        return False
    
    return True

def check_package():
    """Check the built package."""
    print("Checking package...")
    
    return run_command(["twine", "check", "dist/*"], "Checking package")

def upload_to_testpypi():
    """Upload to Test PyPI."""
    print("Uploading to Test PyPI...")
    
    return run_command([
        "twine", "upload", "--repository", "testpypi", "dist/*"
    ], "Uploading to Test PyPI")

def upload_to_pypi():
    """Upload to PyPI."""
    print("Uploading to PyPI...")
    
    confirmation = input("Are you sure you want to upload to PyPI? (yes/no): ")
    if confirmation.lower() != "yes":
        print("Upload cancelled.")
        return False
    
    return run_command(["twine", "upload", "dist/*"], "Uploading to PyPI")

def create_github_release():
    """Create GitHub release."""
    print("Creating GitHub release...")
    
    # Check if gh CLI is available
    result = subprocess.run(["gh", "--version"], capture_output=True)
    if result.returncode != 0:
        print("GitHub CLI (gh) not found. Please create release manually.")
        return False
    
    version = input("Enter version number (e.g., v0.1.0): ")
    title = input("Enter release title: ")
    notes = input("Enter release notes (optional): ")
    
    cmd = ["gh", "release", "create", version, "--title", title]
    if notes:
        cmd.extend(["--notes", notes])
    
    return run_command(cmd, "Creating GitHub release")

def main():
    """Main release function."""
    parser = argparse.ArgumentParser(description="Release MCP Documentation Server")
    parser.add_argument("--clean", action="store_true", help="Clean build directories")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--check", action="store_true", help="Check package")
    parser.add_argument("--test-upload", action="store_true", help="Upload to Test PyPI")
    parser.add_argument("--upload", action="store_true", help="Upload to PyPI")
    parser.add_argument("--github-release", action="store_true", help="Create GitHub release")
    parser.add_argument("--all", action="store_true", help="Run all steps (except upload)")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    success = True
    
    if args.all or args.clean:
        clean_build()
    
    if args.all or args.test:
        success = success and run_tests()
    
    if args.all or args.build:
        success = success and build_package()
    
    if args.all or args.check:
        success = success and check_package()
    
    if args.test_upload and success:
        success = success and upload_to_testpypi()
    
    if args.upload and success:
        success = success and upload_to_pypi()
    
    if args.github_release and success:
        success = success and create_github_release()
    
    if success:
        print("\n" + "=" * 50)
        print("Release process completed successfully!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("Release process failed!")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
