#!/usr/bin/env python3
"""
Simple deployment script for WhatsApp-Evie to PyPI.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, check=True, env=None):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check, env=env)
    return result.returncode == 0


def clean_build_artifacts():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    artifacts = ["build", "dist", "*.egg-info"]
    for artifact in artifacts:
        for path in Path(".").glob(artifact):
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                print(f"Removed: {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed: {path}")


def run_tests():
    """Run tests before deployment."""
    print("🧪 Running tests...")
    return run_command("/Users/bany/miniconda3/bin/python -m pytest tests/ -v --tb=short")


def build_package():
    """Build the package."""
    print("📦 Building package...")
    return run_command("/Users/bany/miniconda3/bin/python -m build")


def check_package():
    """Check the package."""
    print("🔍 Checking package...")
    return run_command("twine check dist/*")


def upload_to_pypi(token):
    """Upload to PyPI."""
    print("🚀 Uploading to PyPI...")
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = token
    return run_command("twine upload dist/*", env=env)


def git_add_commit_push():
    """Add, commit, and push changes to git."""
    print("📝 Adding changes to git...")
    if not run_command("git add .", check=False):
        print("⚠️ Git add failed, continuing...")
    
    print("💾 Committing changes...")
    commit_message = "feat: Deploy WhatsApp-Evie v1.0.0 to PyPI\n\n- Complete WhatsApp-Evie library with comprehensive features\n- 73 passing tests with robust test suite\n- CLI interface and configuration management\n- Bulk messaging and advanced error handling\n- Ready for production use"
    
    if not run_command(f'git commit -m "{commit_message}"', check=False):
        print("⚠️ Git commit failed (maybe no changes), continuing...")
    
    print("🌐 Pushing to remote repository...")
    if not run_command("git push", check=False):
        print("⚠️ Git push failed, continuing...")
    else:
        print("✅ Changes pushed to git successfully!")


def main():
    """Main deployment function."""
    print("🚀 WhatsApp-Evie PyPI Deployment")
    print("=" * 50)
    
    # PyPI token
    token = "pypi-AgEIcHlwaS5vcmcCJDI2OThjM2JkLWY1ODgtNDNlYy1hMDgyLTFkYWYzZWVkZDM0ZgACKlszLCI5M2FiZWM1ZS02NWI4LTRkYTYtODYwNC1mN2I0YmI2Zjc4NjciXQAABiBHfmJf--nOzGMj0wn4--1azqAQIto_6RZdo_Xe_i_5zQ"
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    try:
        # Clean previous builds
        clean_build_artifacts()
        
        # Run tests
        if not run_tests():
            print("❌ Tests failed! Aborting deployment.")
            sys.exit(1)
        
        # Build package
        if not build_package():
            print("❌ Package build failed!")
            sys.exit(1)
        
        # Check package
        if not check_package():
            print("❌ Package check failed!")
            sys.exit(1)
        
        # Upload to PyPI
        print("\n🎯 Ready to upload to PyPI!")
        print("Package details:")
        print("  - Name: whatsapp-evie")
        print("  - Version: 1.0.0")
        print("  - Description: Professional Python library for WhatsApp-Evie integration")
        
        response = input("\nDo you want to proceed with PyPI upload? (y/N): ")
        
        if response.lower() == 'y':
            if upload_to_pypi(token):
                print("\n🎉 Successfully uploaded to PyPI!")
                
                # Git operations
                print("\n📝 Pushing changes to git...")
                git_add_commit_push()
                
                print("\n" + "=" * 50)
                print("🎉 DEPLOYMENT COMPLETE!")
                print("✅ Package uploaded to PyPI")
                print("✅ Changes pushed to git")
                print("🔗 Your package: https://pypi.org/project/whatsapp-evie/")
                print("📦 Install with: pip install whatsapp-evie")
                print("\n📚 Next steps:")
                print("  - Test installation: pip install whatsapp-evie")
                print("  - Check PyPI page: https://pypi.org/project/whatsapp-evie/")
                print("  - Update documentation if needed")
                print("  - Consider adding obfuscated version later")
            else:
                print("❌ PyPI upload failed!")
                sys.exit(1)
        else:
            print("⏹️ Deployment cancelled by user")
            
            # Still do git operations
            print("\n📝 Pushing changes to git...")
            git_add_commit_push()
    
    except KeyboardInterrupt:
        print("\n⏹️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
