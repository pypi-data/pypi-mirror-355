#!/bin/bash
# Build and test script for CryptoPix library

set -e  # Exit on any error

echo "🚀 CryptoPix Library Build and Test Script"
echo "=========================================="

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install build wheel twine

# Install library dependencies
echo "📦 Installing library dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install pytest pytest-cov black flake8

# Run basic functionality test
echo "🧪 Running basic functionality test..."
python3 test_library.py

# Run unit tests if pytest is available
echo "🧪 Running unit tests..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v
else
    echo "⚠️  pytest not available, skipping unit tests"
fi

# Code formatting check
echo "🎨 Checking code formatting..."
if command -v black &> /dev/null; then
    black --check --diff cryptopix/
else
    echo "⚠️  black not available, skipping format check"
fi

# Build the package
echo "🔨 Building package..."
python3 -m build

# List built files
echo "📁 Built files:"
ls -la dist/

echo ""
echo "✅ Build and test completed successfully!"
echo ""
echo "📋 Next steps for publishing:"
echo "1. Test the built package: pip install dist/cryptopix-2.0.0-py3-none-any.whl"
echo "2. Upload to TestPyPI: twine upload --repository testpypi dist/*"
echo "3. Upload to PyPI: twine upload dist/*"
echo ""
echo "🎉 Your CryptoPix library is ready for publishing!"