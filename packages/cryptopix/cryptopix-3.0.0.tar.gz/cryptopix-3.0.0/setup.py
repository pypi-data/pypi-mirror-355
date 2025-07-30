#!/usr/bin/env python3
"""
Setup script for CryptoPix - A secure text-to-image encryption library
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "CryptoPix - Secure text-to-image encryption library"


# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'Pillow>=10.0.0',
        'cryptography>=41.0.0',
        'numpy>=1.24.0',
    ]

setup(
    name="cryptopix",
    version="3.0.0",
    author="CryptoPix Team",
    author_email="founder@cryptopix.com",
    description="Secure text-to-image encryption library using advanced cryptographic techniques",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/cryptopix-official/cryptopix",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'cli': [
            'click>=8.0.0',
            'rich>=13.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'cryptopix=cryptopix.cli.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'cryptopix': ['data/*.csv'],
    },
    keywords="encryption, cryptography, steganography, image, security, text-to-image",
    project_urls={
        "Bug Reports": "https://github.com/cryptopix-official/cryptopix/issues",
        "Source": "https://github.com/cryptopix-official/cryptopix",
        "Documentation": "https://github.com/cryptopix-official/cryptopix",
    },
)