"""
CryptoPix - Secure Text-to-Image Encryption Library

A powerful Python library for encrypting text into images using advanced cryptographic
techniques and converting them back to text with password-based security.

Features:
- Password-derived key generation using PBKDF2-HMAC-SHA256
- Dynamic color table shuffling for enhanced security
- Lossless WebP image generation
- Post-quantum resistance through symmetric cryptography
- Smart key metadata packaging with encryption

Basic Usage:
    >>> from cryptopix import CryptoPix
    >>> cp = CryptoPix()
    >>> 
    >>> # Encrypt text to image
    >>> image_data, smart_key = cp.encrypt("Hello, World!", "my_password")
    >>> 
    >>> # Decrypt image back to text
    >>> from PIL import Image
    >>> import io
    >>> image = Image.open(io.BytesIO(image_data.getvalue()))
    >>> result = cp.decrypt(image, smart_key, "my_password")
    >>> print(result['content'])  # "Hello, World!"

For more advanced usage and examples, see the documentation.
"""

from .core.encryption import CryptoPix
from .core.exceptions import (
    CryptoPixError,
    EncryptionError,
    DecryptionError,
    InvalidPasswordError,
    InvalidKeyError,
    UnsupportedFormatError
)

# Version information
__version__ = "2.0.0"
__author__ = "CryptoPix Team"
__email__ = "support@cryptopix.com"
__license__ = "MIT"

# Main API exports
__all__ = [
    # Main classes
    'CryptoPix',
    
    # Exceptions
    'CryptoPixError',
    'EncryptionError', 
    'DecryptionError',
    'InvalidPasswordError',
    'InvalidKeyError',
    'UnsupportedFormatError',
    
    # Convenience functions
    'encrypt_text',
    'decrypt_image',
    
    # Version info
    '__version__',
]

# Convenience functions for simple usage
def encrypt_text(text, password, width=None):
    """
    Convenience function to encrypt text to image.
    
    Args:
        text (str): Text to encrypt
        password (str): Password for encryption
        width (int, optional): Image width in pixels
        
    Returns:
        tuple: (image_data, smart_key) where image_data is BytesIO object
        
    Example:
        >>> image_data, smart_key = encrypt_text("Secret message", "password123")
        >>> with open("encrypted.webp", "wb") as f:
        ...     f.write(image_data.getvalue())
    """
    cp = CryptoPix()
    return cp.encrypt(text, password, width)

def decrypt_image(image, smart_key, password):
    """
    Convenience function to decrypt image to text.
    
    Args:
        image (PIL.Image.Image): Image to decrypt
        smart_key (str): Smart key from encryption
        password (str): Password used for encryption
        
    Returns:
        dict: Decryption result with 'content' and 'type' keys
        
    Example:
        >>> from PIL import Image
        >>> image = Image.open("encrypted.webp")
        >>> result = decrypt_image(image, smart_key, "password123")
        >>> print(result['content'])
    """
    cp = CryptoPix()
    return cp.decrypt(image, smart_key, password)