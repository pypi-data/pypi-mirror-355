# Code Obfuscation with PyArmor

This document explains how to create obfuscated versions of the WhatsApp-Evie library using PyArmor for enhanced code protection.

## Overview

PyArmor is used to obfuscate the Python source code, making it difficult to reverse engineer while maintaining full functionality. This is particularly useful for commercial distributions or when you want to protect intellectual property.

## Features

- **Code Obfuscation**: Python bytecode and source code protection
- **String Obfuscation**: Sensitive strings are encrypted
- **Import Protection**: Module imports are obfuscated
- **Runtime Protection**: Anti-debug and anti-dump mechanisms
- **License Control**: Optional license and usage restrictions

## Prerequisites

```bash
pip install pyarmor>=8.0.0
```

## Quick Start

### 1. Create Obfuscated Package

```bash
# Using the provided script
python scripts/build_obfuscated.py --all

# Or manually
pyarmor gen --output dist-obfuscated --recursive whatsapp_evie
```

### 2. Build and Publish

```bash
# Build obfuscated version only
python scripts/build_and_publish.py --obfuscate --build

# Full release with obfuscation
python scripts/build_and_publish.py --release-obfuscated
```

## Configuration

### PyArmor Configuration File

The `pyarmor.cfg` file contains obfuscation settings:

```ini
[pyarmor]
mode = advanced

includes = 
    whatsapp_evie/*.py
    whatsapp_evie/**/*.py

excludes = 
    whatsapp_evie/__init__.py
    tests/*
    examples/*

[obfuscate]
enable_code_obfuscation = true
enable_string_obfuscation = true
enable_import_obfuscation = true
enable_function_obfuscation = true
enable_variable_obfuscation = true

[runtime]
enable_runtime_key = true
enable_anti_debug = true
enable_anti_dump = true
```

### Obfuscation Modes

- **basic**: Basic obfuscation with minimal protection
- **advanced**: Strong protection with runtime checks
- **super**: Maximum protection with hardware binding

## Manual Obfuscation Process

### 1. Clean Previous Artifacts

```bash
rm -rf dist-obfuscated whatsapp_evie_obfuscated .pyarmor
```

### 2. Generate Obfuscated Code

```bash
pyarmor gen \
    --output dist-obfuscated \
    --recursive \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    --exclude "tests" \
    --exclude "examples" \
    whatsapp_evie
```

### 3. Create Package Structure

```bash
mkdir -p whatsapp_evie_obfuscated
cp -r dist-obfuscated/* whatsapp_evie_obfuscated/
cp setup.py pyproject.toml README.md LICENSE requirements.txt whatsapp_evie_obfuscated/
```

### 4. Update Package Metadata

Modify `setup.py` in the obfuscated directory:

```python
# Update package name
name="whatsapp-evie-obfuscated"

# Add runtime files to package data
package_data={
    "whatsapp_evie": ["pyarmor_runtime_*"],
}
```

### 5. Build Package

```bash
cd whatsapp_evie_obfuscated
python -m build
```

## Advanced Configuration

### License Control

Add license restrictions to the obfuscated package:

```bash
# Expire after 1 year
pyarmor gen --expire-date 2025-12-31 whatsapp_evie

# Bind to hardware
pyarmor gen --bind-hardware whatsapp_evie

# Limit number of uses
pyarmor gen --max-uses 1000 whatsapp_evie
```

### Custom Runtime Key

Generate a custom runtime key for additional security:

```bash
pyarmor gen --runtime-key "your-secret-key" whatsapp_evie
```

### Platform-Specific Builds

Create platform-specific obfuscated packages:

```bash
# Linux x86_64
pyarmor gen --platform linux.x86_64 whatsapp_evie

# Windows x86_64
pyarmor gen --platform windows.x86_64 whatsapp_evie

# macOS x86_64
pyarmor gen --platform darwin.x86_64 whatsapp_evie
```

## Testing Obfuscated Package

### 1. Install Locally

```bash
cd whatsapp_evie_obfuscated
pip install -e .
```

### 2. Run Tests

```bash
# Test basic functionality
python -c "from whatsapp_evie import WhatsAppEvieClient; print('Import successful')"

# Run full test suite
pytest tests/
```

### 3. Verify Obfuscation

Check that the installed package contains obfuscated code:

```bash
python -c "
import whatsapp_evie.client
import inspect
print(inspect.getsource(whatsapp_evie.client.WhatsAppEvieClient))
"
```

You should see obfuscated code instead of readable source.

## Distribution

### PyPI Distribution

The obfuscated package can be distributed on PyPI like any other package:

```bash
twine upload dist/*
```

### Private Distribution

For private distribution, you can:

1. Host on a private PyPI server
2. Distribute as wheel files
3. Use git repositories with access control

## Security Considerations

### What PyArmor Protects

- ✅ Source code visibility
- ✅ String literals and constants
- ✅ Function and variable names
- ✅ Import statements
- ✅ Runtime tampering (with advanced mode)

### What PyArmor Doesn't Protect

- ❌ Network traffic (use HTTPS/TLS)
- ❌ API keys in environment variables
- ❌ Data at rest (use encryption)
- ❌ Determined reverse engineering (adds significant difficulty)

### Best Practices

1. **Combine with Other Security Measures**:
   - Use environment variables for secrets
   - Implement proper authentication
   - Use HTTPS for all communications

2. **Regular Updates**:
   - Update PyArmor regularly
   - Regenerate obfuscated packages periodically

3. **Testing**:
   - Always test obfuscated packages thoroughly
   - Verify functionality across different environments

4. **Documentation**:
   - Document the obfuscation process
   - Keep track of obfuscation settings used

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure runtime files are included
   python -c "import whatsapp_evie; print(whatsapp_evie.__file__)"
   ```

2. **Performance Issues**:
   ```bash
   # Use basic mode for better performance
   pyarmor gen --mode basic whatsapp_evie
   ```

3. **Compatibility Issues**:
   ```bash
   # Exclude problematic files
   pyarmor gen --exclude "problematic_module.py" whatsapp_evie
   ```

### Debug Mode

Run PyArmor in debug mode for troubleshooting:

```bash
pyarmor gen --debug whatsapp_evie
```

## CI/CD Integration

The GitHub Actions workflow automatically creates obfuscated packages:

```yaml
- name: Obfuscate code with PyArmor
  run: |
    pyarmor gen --output dist-obfuscated whatsapp_evie
    # Additional processing...
```

## License Compliance

Ensure PyArmor usage complies with:

- PyArmor license terms
- Your project's license
- Distribution platform requirements
- Local regulations

## Support

For PyArmor-specific issues:
- [PyArmor Documentation](https://pyarmor.readthedocs.io/)
- [PyArmor GitHub](https://github.com/dashingsoft/pyarmor)

For WhatsApp-Evie obfuscation issues:
- Create an issue in the project repository
- Contact: contact@evolvis.ai
