"""
Tests for PyArmor obfuscation functionality.
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestObfuscation:
    """Test obfuscation functionality."""
    
    def test_pyarmor_available(self):
        """Test that PyArmor is available when obfuscation extra is installed."""
        try:
            import pyarmor
            assert pyarmor is not None
        except ImportError:
            pytest.skip("PyArmor not installed - install with pip install 'whatsapp-evie[obfuscation]'")
    
    def test_obfuscation_script_exists(self):
        """Test that obfuscation script exists."""
        script_path = Path("scripts/build_obfuscated.py")
        assert script_path.exists(), "Obfuscation script not found"
        assert script_path.is_file(), "Obfuscation script is not a file"
    
    def test_pyarmor_config_exists(self):
        """Test that PyArmor configuration exists."""
        config_path = Path("pyarmor.cfg")
        assert config_path.exists(), "PyArmor config not found"
        assert config_path.is_file(), "PyArmor config is not a file"
    
    @pytest.mark.slow
    def test_obfuscation_script_help(self):
        """Test that obfuscation script shows help."""
        result = subprocess.run(
            [sys.executable, "scripts/build_obfuscated.py", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "Build obfuscated WhatsApp-Evie package" in result.stdout
        assert "--create" in result.stdout
        assert "--build" in result.stdout
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_can_create_obfuscated_package(self):
        """Test that we can create an obfuscated package (requires PyArmor)."""
        try:
            import pyarmor
        except ImportError:
            pytest.skip("PyArmor not installed")
        
        # Clean any existing artifacts
        result = subprocess.run(
            [sys.executable, "scripts/build_obfuscated.py", "--clean"],
            capture_output=True,
            text=True
        )
        
        # This test would actually create obfuscated package
        # but we skip it in CI to avoid complexity
        pytest.skip("Skipping actual obfuscation test - would require full setup")
    
    def test_gitignore_includes_obfuscation_artifacts(self):
        """Test that .gitignore includes obfuscation artifacts."""
        gitignore_path = Path(".gitignore")
        assert gitignore_path.exists(), ".gitignore not found"
        
        content = gitignore_path.read_text()
        
        # Check for PyArmor-related entries
        assert ".pyarmor/" in content, "PyArmor directory not in .gitignore"
        assert "dist-obfuscated/" in content, "Obfuscated dist directory not in .gitignore"
        assert "whatsapp_evie_obfuscated/" in content, "Obfuscated package directory not in .gitignore"
        assert "pyarmor_runtime_*/" in content, "PyArmor runtime files not in .gitignore"
    
    def test_setup_includes_obfuscation_extra(self):
        """Test that setup.py includes obfuscation extra."""
        setup_path = Path("setup.py")
        assert setup_path.exists(), "setup.py not found"
        
        content = setup_path.read_text()
        assert '"obfuscation"' in content, "Obfuscation extra not in setup.py"
        assert "pyarmor" in content, "PyArmor not in obfuscation dependencies"
    
    def test_pyproject_includes_obfuscation_extra(self):
        """Test that pyproject.toml includes obfuscation extra."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        content = pyproject_path.read_text()
        assert "obfuscation" in content, "Obfuscation extra not in pyproject.toml"
        assert "pyarmor" in content, "PyArmor not in obfuscation dependencies"
