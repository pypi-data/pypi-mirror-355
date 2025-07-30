#!/usr/bin/env python3
"""
Build obfuscated package with PyArmor for WhatsApp-Evie.

This script creates an obfuscated version of the package for distribution.
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path


def run_command(command, check=True, cwd=None):
    """Run a shell command."""
    print(f"Running: {command}")
    if cwd:
        print(f"Working directory: {cwd}")
    result = subprocess.run(command, shell=True, check=check, cwd=cwd)
    return result.returncode == 0


def clean_obfuscated_artifacts():
    """Clean previous obfuscated artifacts."""
    print("Cleaning previous obfuscated artifacts...")
    
    artifacts = [
        "dist-obfuscated",
        "whatsapp_evie_obfuscated",
        ".pyarmor",
        "pyarmor_runtime_000000"
    ]
    
    for artifact in artifacts:
        for path in Path(".").glob(artifact):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed file: {path}")


def create_obfuscated_package():
    """Create obfuscated package with PyArmor."""
    print("Creating obfuscated package...")
    
    # Clean previous artifacts
    clean_obfuscated_artifacts()
    
    # Create output directory
    output_dir = Path("dist-obfuscated")
    output_dir.mkdir(exist_ok=True)
    
    # Obfuscate the main package
    print("Obfuscating whatsapp_evie package...")

    # Try PyArmor 8.x syntax first, then fall back to 7.x
    cmd_v8 = [
        "pyarmor", "gen",
        "--output", str(output_dir),
        "--recursive",
        "--exclude", "__pycache__",
        "--exclude", "*.pyc",
        "--exclude", "tests",
        "--exclude", "examples",
        "whatsapp_evie"
    ]

    cmd_v7 = [
        "pyarmor", "obfuscate",
        "--output", str(output_dir),
        "--recursive",
        "whatsapp_evie"
    ]

    # Try PyArmor 8.x first
    print("Trying PyArmor 8.x syntax...")
    if run_command(" ".join(cmd_v8), check=False):
        print(f"✅ Package obfuscated successfully with PyArmor 8.x")
    elif run_command(" ".join(cmd_v7), check=False):
        print(f"✅ Package obfuscated successfully with PyArmor 7.x")
    else:
        print("❌ Failed to obfuscate package with both PyArmor versions")
        return False
    
    # Create package structure
    pkg_dir = Path("whatsapp_evie_obfuscated")
    pkg_dir.mkdir(exist_ok=True)
    
    # Copy obfuscated files
    obfuscated_pkg = output_dir / "whatsapp_evie"
    if obfuscated_pkg.exists():
        shutil.copytree(obfuscated_pkg, pkg_dir / "whatsapp_evie", dirs_exist_ok=True)
    
    # Copy runtime files
    for runtime_file in output_dir.glob("pyarmor_runtime_*"):
        shutil.copy2(runtime_file, pkg_dir / "whatsapp_evie")
    
    # Copy package metadata files
    metadata_files = [
        "setup.py",
        "pyproject.toml", 
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "requirements.txt",
        "MANIFEST.in"
    ]
    
    for file_name in metadata_files:
        src_file = Path(file_name)
        if src_file.exists():
            shutil.copy2(src_file, pkg_dir)
    
    # Copy directories (but not their contents for some)
    dirs_to_copy = {
        "tests": True,  # Copy tests for validation
        "examples": True,  # Copy examples
        "docs": True,  # Copy docs
    }
    
    for dir_name, copy_contents in dirs_to_copy.items():
        src_dir = Path(dir_name)
        if src_dir.exists():
            if copy_contents:
                shutil.copytree(src_dir, pkg_dir / dir_name, dirs_exist_ok=True)
            else:
                (pkg_dir / dir_name).mkdir(exist_ok=True)
    
    # Create modified __init__.py for obfuscated package
    create_obfuscated_init(pkg_dir / "whatsapp_evie")
    
    # Update setup.py for obfuscated version
    update_setup_for_obfuscated(pkg_dir)
    
    print(f"Obfuscated package created in: {pkg_dir}")
    return True


def create_obfuscated_init(pkg_dir):
    """Create __init__.py for obfuscated package."""
    init_file = pkg_dir / "__init__.py"
    
    # Read original __init__.py
    original_init = Path("whatsapp_evie") / "__init__.py"
    original_content = ""
    if original_init.exists():
        original_content = original_init.read_text()
    
    # Create new __init__.py with PyArmor runtime import
    new_content = '''"""
WhatsApp-Evie Integration Library (Obfuscated)

This is the obfuscated version of the WhatsApp-Evie library.
"""

# Import PyArmor runtime
try:
    from .pyarmor_runtime_000000 import __pyarmor__
except ImportError:
    # Fallback if runtime not found
    pass

'''
    
    # Add original exports (but not the docstring and imports that might conflict)
    lines = original_content.split('\n')
    in_docstring = False
    docstring_quotes = None
    
    for line in lines:
        stripped = line.strip()
        
        # Skip docstring
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            docstring_quotes = stripped[:3]
            if stripped.count(docstring_quotes) >= 2:
                in_docstring = False
            continue
        elif in_docstring:
            if docstring_quotes in line:
                in_docstring = False
            continue
        
        # Skip imports that might conflict
        if (stripped.startswith('from .') or 
            stripped.startswith('import ') or
            stripped.startswith('__version__') or
            stripped.startswith('__author__') or
            stripped.startswith('__email__') or
            stripped.startswith('__license__')):
            new_content += line + '\n'
    
    init_file.write_text(new_content)
    print(f"Created obfuscated __init__.py: {init_file}")


def update_setup_for_obfuscated(pkg_dir):
    """Update setup.py for obfuscated version."""
    setup_file = pkg_dir / "setup.py"
    
    if not setup_file.exists():
        return
    
    content = setup_file.read_text()
    
    # Add note about obfuscation in description
    content = content.replace(
        'description="A professional Python library for WhatsApp-Evie integration',
        'description="A professional Python library for WhatsApp-Evie integration (Obfuscated)'
    )
    
    # Update package name to indicate obfuscated version
    content = content.replace(
        'name="whatsapp-evie"',
        'name="whatsapp-evie-obfuscated"'
    )
    
    # Add PyArmor runtime to package data
    if 'include_package_data=True' in content:
        # Add package data specification
        package_data_addition = '''
    package_data={
        "whatsapp_evie": ["pyarmor_runtime_*"],
    },'''
        content = content.replace(
            'include_package_data=True,',
            'include_package_data=True,' + package_data_addition
        )
    
    setup_file.write_text(content)
    print(f"Updated setup.py for obfuscated version: {setup_file}")


def build_obfuscated_package():
    """Build the obfuscated package."""
    pkg_dir = Path("whatsapp_evie_obfuscated")
    
    if not pkg_dir.exists():
        print("Obfuscated package directory not found. Run create_obfuscated_package first.")
        return False
    
    print("Building obfuscated package...")
    
    # Build the package
    if not run_command("python -m build", cwd=pkg_dir):
        print("Failed to build obfuscated package")
        return False
    
    # Copy built packages to main dist directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    obf_dist_dir = pkg_dir / "dist"
    if obf_dist_dir.exists():
        for file in obf_dist_dir.glob("*"):
            shutil.copy2(file, dist_dir)
            print(f"Copied {file.name} to dist/")
    
    return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build obfuscated WhatsApp-Evie package")
    parser.add_argument("--clean", action="store_true", help="Clean obfuscated artifacts")
    parser.add_argument("--create", action="store_true", help="Create obfuscated package")
    parser.add_argument("--build", action="store_true", help="Build obfuscated package")
    parser.add_argument("--all", action="store_true", help="Clean, create, and build")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    success = True
    
    if args.clean or args.all:
        clean_obfuscated_artifacts()
    
    if args.create or args.all:
        if not create_obfuscated_package():
            success = False
    
    if args.build or args.all:
        if success and not build_obfuscated_package():
            success = False
    
    if success:
        print("Obfuscated package operations completed successfully!")
        print("Files available in dist/ directory:")
        dist_dir = Path("dist")
        if dist_dir.exists():
            for file in dist_dir.glob("*"):
                print(f"  - {file.name}")
    else:
        print("Some operations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
