# CryptoPix - Commercial Text-to-Image Encryption Library

![CryptoPix Logo](https://img.shields.io/badge/CryptoPix-v2.0.0-blue)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Commercial-red)

A powerful commercial Python library for encrypting text into images using advanced cryptographic techniques and converting them back to text with password-based security.

**© 2025 CryptoPix Team. All rights reserved. This software is proprietary and requires a commercial license for use.**

## 🔐 Features

- **Advanced Encryption**: Password-derived key generation using PBKDF2-HMAC-SHA256
- **Secure Key Management**: Dynamic color table shuffling based on derived keys
- **Lossless Compression**: WebP image generation with no data loss
- **Post-Quantum Resistance**: Symmetric cryptography designed for future security
- **Smart Key System**: Encrypted metadata packaging for enhanced security
- **Simple API**: Easy-to-use interface for developers
- **Command Line Tool**: Built-in CLI for terminal usage

## 🚀 Quick Start

### Installation

```bash
pip install cryptopix
```

### Basic Usage

```python
from cryptopix import CryptoPix

# Initialize
cp = CryptoPix()

# Encrypt text to image
image_data, smart_key = cp.encrypt("Hello, World!", "my_password")

# Save encrypted image
with open("encrypted.webp", "wb") as f:
    f.write(image_data.getvalue())

# Decrypt image back to text
from PIL import Image
image = Image.open("encrypted.webp")
result = cp.decrypt(image, smart_key, "my_password")
print(result['content'])  # "Hello, World!"
```

### Convenience Functions

```python
from cryptopix import encrypt_text, decrypt_image
from PIL import Image

# Quick encryption
image_data, smart_key = encrypt_text("Secret message", "password123")

# Quick decryption
image = Image.open("encrypted.webp")
result = decrypt_image(image, smart_key, "password123")
```

## 🖥️ Command Line Usage

### Encrypt text to image
```bash
cryptopix encrypt -t "Hello World" -p mypassword -o encrypted.webp
```

### Encrypt file contents
```bash
cryptopix encrypt -f input.txt -p mypassword -o encrypted.webp
```

### Decrypt image to text
```bash
cryptopix decrypt -i encrypted.webp -k "cryptopix_v2:..." -p mypassword
```

### Decrypt and save to file
```bash
cryptopix decrypt -i encrypted.webp -k "cryptopix_v2:..." -p mypassword -o output.txt
```

## 📚 Advanced Usage

### Custom Image Dimensions

```python
from cryptopix import CryptoPix

cp = CryptoPix()

# Specify custom width
image_data, smart_key = cp.encrypt("Long text content", "password", width=100)
```

### Error Handling

```python
from cryptopix import CryptoPix
from cryptopix.core.exceptions import (
    EncryptionError, 
    DecryptionError, 
    InvalidPasswordError
)

cp = CryptoPix()

try:
    image_data, smart_key = cp.encrypt("text", "password")
except EncryptionError as e:
    print(f"Encryption failed: {e}")

try:
    result = cp.decrypt(image, smart_key, "wrong_password")
except InvalidPasswordError:
    print("Incorrect password provided")
except DecryptionError as e:
    print(f"Decryption failed: {e}")
```

### Working with Binary Data

```python
# The library can handle binary data too
import base64

# If decryption returns binary data
result = cp.decrypt(image, smart_key, "password")
if result['type'] == 'binary':
    binary_data = base64.b64decode(result['content'])
    # Process binary data
```

## 🔧 API Reference

### CryptoPix Class

#### `encrypt(text: str, password: str, width: int = None) -> tuple`
Encrypt text into a WebP image.

**Parameters:**
- `text`: Plain-text data to encrypt
- `password`: User-provided password
- `width`: Optional image width (auto-calculated if None)

**Returns:** Tuple of (BytesIO image data, smart_key string)

#### `decrypt(img: Image.Image, smart_key: str, password: str) -> dict`
Decrypt an encrypted WebP image back to text.

**Parameters:**
- `img`: PIL Image object
- `smart_key`: Smart key from encryption process
- `password`: Same password used for encryption

**Returns:** Dictionary with 'content', 'type', and 'success' keys

### Exception Classes

- `CryptoPixError`: Base exception for all CryptoPix errors
- `EncryptionError`: Raised when encryption fails
- `DecryptionError`: Raised when decryption fails
- `InvalidPasswordError`: Raised when password is incorrect
- `InvalidKeyError`: Raised when smart key is invalid
- `UnsupportedFormatError`: Raised for unsupported file formats

## 🔒 Security Features

### Cryptographic Strength
- **PBKDF2-HMAC-SHA256** with 100,000 iterations
- **AES-256-GCM** for metadata encryption
- **256-bit derived keys** from user passwords
- **128-bit random salts** for each encryption

### Post-Quantum Resistance
- Symmetric cryptography design
- No reliance on factoring or discrete logarithm problems
- Future-proof against quantum computer attacks

### Security Best Practices
- Constant-time operations where possible
- Secure random number generation
- Memory-safe implementations
- No key material stored in plaintext

## 📋 Requirements

- Python 3.8 or higher
- Pillow (PIL) >= 10.0.0
- cryptography >= 41.0.0
- numpy >= 1.24.0

## 🔧 Development Setup

```bash
git clone https://github.com/cryptopix/cryptopix-python.git
cd cryptopix-python

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy cryptopix/
```

## 📊 Performance

### Benchmarks
- **Small text** (< 100 chars): ~10ms encryption, ~5ms decryption
- **Medium text** (1KB): ~50ms encryption, ~25ms decryption  
- **Large text** (10KB): ~200ms encryption, ~100ms decryption

### Memory Usage
- **Efficient chunking**: 24-bit color mapping
- **LRU caching**: Optimized for repeated operations
- **Streaming**: Large files processed without full memory load

## 💳 Commercial Licensing

CryptoPix is a commercial software product. Different licensing options are available:

### 📋 License Types

#### Evaluation License (FREE - 30 days)
- Personal evaluation and testing only
- Non-production environments
- Limited to 30 days usage
- No commercial deployment

#### Developer License ($299/year)
- Single developer use
- Development and testing environments
- Up to 1,000 API calls per month
- Email support

#### Professional License ($999/year)
- Team use (up to 5 developers)
- Production deployment allowed
- Up to 100,000 API calls per month
- Priority support and documentation

#### Enterprise License (Custom pricing)
- Unlimited developers and deployments
- Unlimited API calls
- Custom integrations and features
- Dedicated support and SLA
- On-premise deployment options

### 🛒 Getting a License

1. **Contact Sales**: Email founderg@cryptopix.com
2. **Specify Requirements**: Development team size, expected usage
3. **Receive Quote**: Custom pricing based on your needs
4. **License Delivery**: Receive license key and documentation

### 📄 License Terms

This software is proprietary and confidential. Key restrictions include:
- No distribution or sublicensing without permission
- No reverse engineering or modification
- Production use requires valid commercial license
- Evaluation limited to 30 days

For complete terms, see the [LICENSE](LICENSE) file.

## 🛡️ Security

For security concerns, please email founder@cryptopix.in instead of using the issue tracker.

## 📞 Support

- **Sales Inquiries**: founder@cryptopix.in
- **Technical Support**: founder@cryptopix.in
- **Security Issues**: founder@cryptopix.in

## 🎯 Roadmap

- [ ] Support for additional image formats (PNG, JPEG)
- [ ] Hardware acceleration for large files
- [ ] Integration with cloud storage providers
- [ ] Mobile SDK development
- [ ] Enterprise key management integration

---

**Made with ❤️ by the CryptoPix Team**