#!/usr/bin/env python3
"""
Build and publish script for WhatsApp-Evie package.

This script helps with building and publishing the package to PyPI.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, check=True, env=None):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check, env=env)
    return result.returncode == 0


def clean_build_artifacts():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    artifacts = [
        "build",
        "dist", 
        "*.egg-info",
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov"
    ]
    
    for artifact in artifacts:
        for path in Path(".").glob(artifact):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed file: {path}")


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    return run_command("pytest tests/ -v --cov=whatsapp_evie")


def run_quality_checks():
    """Run code quality checks."""
    print("Running code quality checks...")
    
    checks = [
        "black --check whatsapp_evie tests examples",
        "isort --check-only whatsapp_evie tests examples", 
        "flake8 whatsapp_evie",
        "mypy whatsapp_evie"
    ]
    
    for check in checks:
        if not run_command(check, check=False):
            print(f"Quality check failed: {check}")
            return False
    
    return True


def build_package():
    """Build the package."""
    print("Building package...")
    return run_command("python -m build")


def check_package():
    """Check the built package."""
    print("Checking package...")
    return run_command("twine check dist/*")


def upload_to_test_pypi():
    """Upload to Test PyPI."""
    print("Uploading to Test PyPI...")
    return run_command("twine upload --repository testpypi dist/*")


def upload_to_pypi(token=None):
    """Upload to PyPI."""
    print("Uploading to PyPI...")

    if token:
        # Use token for authentication
        env = os.environ.copy()
        env["TWINE_USERNAME"] = "__token__"
        env["TWINE_PASSWORD"] = token
        return run_command("twine upload dist/*", env=env)
    else:
        return run_command("twine upload dist/*")


def create_obfuscated_package():
    """Create obfuscated package using PyArmor."""
    print("Creating obfuscated package...")
    return run_command("python scripts/build_obfuscated.py --all")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build and publish WhatsApp-Evie package")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--quality", action="store_true", help="Run quality checks")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--check", action="store_true", help="Check package")
    parser.add_argument("--test-upload", action="store_true", help="Upload to Test PyPI")
    parser.add_argument("--upload", action="store_true", help="Upload to PyPI")
    parser.add_argument("--obfuscate", action="store_true", help="Create obfuscated version")
    parser.add_argument("--all", action="store_true", help="Run all steps except upload")
    parser.add_argument("--release", action="store_true", help="Full release (all steps + upload)")
    parser.add_argument("--release-obfuscated", action="store_true", help="Full release with obfuscation")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    success = True
    
    if args.clean or args.all or args.release:
        clean_build_artifacts()
    
    if args.test or args.all or args.release:
        if not run_tests():
            print("Tests failed!")
            success = False
    
    if args.quality or args.all or args.release:
        if not run_quality_checks():
            print("Quality checks failed!")
            success = False
    
    if args.obfuscate or args.release_obfuscated:
        if success and not create_obfuscated_package():
            print("Obfuscation failed!")
            success = False

    if args.build or args.all or args.release or args.release_obfuscated:
        if success and not build_package():
            print("Build failed!")
            success = False
    
    if args.check or args.all or args.release or args.release_obfuscated:
        if success and not check_package():
            print("Package check failed!")
            success = False
    
    if args.test_upload and success:
        if not upload_to_test_pypi():
            print("Test upload failed!")
            success = False
    
    if args.upload or args.release or args.release_obfuscated:
        if success:
            package_type = "obfuscated " if args.release_obfuscated else ""
            response = input(f"Are you sure you want to upload {package_type}package to PyPI? (y/N): ")
            if response.lower() == 'y':
                if not upload_to_pypi():
                    print("Upload failed!")
                    success = False
                else:
                    print(f"Successfully uploaded {package_type}package to PyPI!")
            else:
                print("Upload cancelled.")
        else:
            print("Skipping upload due to previous failures.")
    
    if success:
        print("All operations completed successfully!")
    else:
        print("Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
