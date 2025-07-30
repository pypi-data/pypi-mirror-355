# CryptoPix Library Publishing Guide

This guide walks you through the process of publishing the CryptoPix library to PyPI.

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **PyPI account** - Sign up at [pypi.org](https://pypi.org)
3. **TestPyPI account** (optional but recommended) - Sign up at [test.pypi.org](https://test.pypi.org)

## 🚀 Quick Start

### 1. Prepare Your Environment

```bash
# Clone/navigate to the library directory
cd cryptopix_lib

# Make build script executable
chmod +x build_and_test.sh

# Run the automated build and test script
./build_and_test.sh
```

### 2. Manual Build Process (Alternative)

If you prefer manual control:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip build wheel twine
pip install -r requirements.txt

# Test the library
python3 test_library.py

# Build the package
python3 -m build
```

### 3. Test Installation Locally

```bash
# Install the built package locally
pip install dist/cryptopix-2.0.0-py3-none-any.whl

# Test it works
python3 -c "from cryptopix import CryptoPix; print('✅ Import successful')"
```

## 📤 Publishing Process

### Step 1: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Install from TestPyPI to test
pip install --index-url https://test.pypi.org/simple/ cryptopix
```

### Step 2: Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

### Step 3: Verify Publication

```bash
# Install from PyPI
pip install cryptopix

# Test the installation
python3 -c "from cryptopix import CryptoPix; cp = CryptoPix(); print('🎉 Published successfully!')"
```

## 🔧 Configuration Files

### `pyproject.toml`
Modern Python packaging configuration with:
- Project metadata
- Dependencies
- Build system configuration
- Development tool settings

### `setup.py` 
Legacy packaging support for broader compatibility.

### `MANIFEST.in`
Specifies additional files to include in the distribution.

## 📁 Library Structure

```
cryptopix_lib/
├── cryptopix/                 # Main library package
│   ├── __init__.py           # Package initialization & public API
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── encryption.py     # Main CryptoPix class
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── mapping.py        # Color mapping utilities
│   │   └── utils.py          # Utility functions
│   └── cli/                  # Command-line interface
│       ├── __init__.py
│       └── main.py           # CLI implementation
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_encryption.py    # Core tests
│   └── test_examples.py      # Example/integration tests
├── README.md                 # Library documentation
├── LICENSE                   # MIT license
├── pyproject.toml           # Modern packaging config
├── setup.py                 # Legacy packaging config
├── requirements.txt         # Dependencies
├── test_library.py          # Verification script
└── build_and_test.sh        # Automated build script
```

## 🎯 Publishing Checklist

### Before Publishing:
- [ ] Test all functionality with `python3 test_library.py`
- [ ] Run unit tests with `pytest tests/`
- [ ] Verify package builds correctly with `python3 -m build`
- [ ] Test installation from built wheel
- [ ] Update version number if needed
- [ ] Review README.md for accuracy
- [ ] Ensure LICENSE file is included

### Publishing Steps:
- [ ] Upload to TestPyPI first
- [ ] Install and test from TestPyPI
- [ ] Upload to PyPI
- [ ] Verify installation from PyPI
- [ ] Test CLI functionality: `cryptopix --help`

### Post-Publishing:
- [ ] Update documentation with installation instructions
- [ ] Create GitHub release (if using GitHub)
- [ ] Announce the release
- [ ] Monitor for issues and feedback

## 🛠️ Advanced Configuration

### Custom PyPI Repositories

Configure `.pypirc` for easier uploads:

```ini
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = <your-pypi-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-testpypi-token>
```

### Version Management

Update version in multiple places:
- `pyproject.toml` - `version = "x.x.x"`
- `setup.py` - `version="x.x.x"`
- `cryptopix/__init__.py` - `__version__ = "x.x.x"`

### Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

## 🚨 Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure all `__init__.py` files are present
2. **Missing Dependencies**: Check `requirements.txt` is complete
3. **Upload Conflicts**: Version already exists on PyPI
4. **Authentication**: Verify PyPI tokens are correct

### Build Issues:

```bash
# Clean build artifacts
rm -rf build/ dist/ *.egg-info/

# Rebuild
python3 -m build
```

### Test Issues:

```bash
# Install in development mode
pip install -e .

# Run specific tests
pytest tests/test_encryption.py -v
```

## 📞 Support

- **Documentation**: Include link to your documentation
- **Issues**: GitHub issues or support email
- **Community**: Discord, forums, or mailing list

## 🎉 Success!

Once published, users can install your library with:

```bash
pip install cryptopix
```

And use it in their projects:

```python
from cryptopix import CryptoPix

cp = CryptoPix()
image_data, smart_key = cp.encrypt("Hello, World!", "password")
# Your library is now available worldwide! 🌍
```