#!/usr/bin/env python3
"""
Setup development environment for WhatsApp-Evie.

This script helps set up the development environment with correct dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result.returncode == 0


def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print("✅ Python version is compatible")
    return True


def install_dependencies():
    """Install development dependencies."""
    print("Installing development dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip"):
        print("❌ Failed to upgrade pip")
        return False
    
    # Install main dependencies
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        print("❌ Failed to install main dependencies")
        return False
    
    # Install development dependencies
    if not run_command(f"{sys.executable} -m pip install -r dev-requirements.txt"):
        print("❌ Failed to install development dependencies")
        return False
    
    # Install package in development mode
    if not run_command(f"{sys.executable} -m pip install -e ."):
        print("❌ Failed to install package in development mode")
        return False
    
    print("✅ Dependencies installed successfully")
    return True


def verify_installation():
    """Verify that the installation works."""
    print("Verifying installation...")
    
    # Test basic import
    try:
        import whatsapp_evie
        print(f"✅ Package imported successfully (version: {whatsapp_evie.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import package: {e}")
        return False
    
    # Test pytest
    try:
        import pytest
        print(f"✅ pytest available (version: {pytest.__version__})")
    except ImportError as e:
        print(f"❌ pytest not available: {e}")
        return False
    
    # Test pytest-asyncio
    try:
        import pytest_asyncio
        print(f"✅ pytest-asyncio available (version: {pytest_asyncio.__version__})")
    except ImportError as e:
        print(f"❌ pytest-asyncio not available: {e}")
        return False
    
    return True


def run_tests():
    """Run the test suite."""
    print("Running test suite...")
    
    # Run tests with verbose output
    cmd = f"{sys.executable} -m pytest tests/ -v --tb=short"
    
    if run_command(cmd, check=False):
        print("✅ All tests passed")
        return True
    else:
        print("❌ Some tests failed")
        return False


def setup_pre_commit():
    """Setup pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    
    if not run_command("pre-commit install"):
        print("❌ Failed to install pre-commit hooks")
        return False
    
    print("✅ Pre-commit hooks installed")
    return True


def main():
    """Main function."""
    print("🚀 Setting up WhatsApp-Evie development environment")
    print("=" * 60)
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    print()
    
    # Verify installation
    if not verify_installation():
        sys.exit(1)
    
    print()
    
    # Setup pre-commit
    if not setup_pre_commit():
        print("⚠️ Pre-commit setup failed, but continuing...")
    
    print()
    
    # Run tests
    print("Running initial test to verify everything works...")
    if run_tests():
        print("\n🎉 Development environment setup complete!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your API credentials")
        print("2. Run tests: python -m pytest tests/ -v")
        print("3. Start developing!")
    else:
        print("\n⚠️ Setup complete but some tests failed.")
        print("This might be due to missing API credentials or configuration.")
        print("Check the test output above for details.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
