"""
CryptoPix Exception Classes

This module defines custom exceptions used throughout the CryptoPix library.
"""


class CryptoPixError(Exception):
    """Base exception class for all CryptoPix errors."""
    pass


class EncryptionError(CryptoPixError):
    """Raised when encryption operation fails."""
    pass


class DecryptionError(CryptoPixError):
    """Raised when decryption operation fails."""
    pass


class InvalidPasswordError(DecryptionError):
    """Raised when an invalid password is provided for decryption."""
    pass


class InvalidKeyError(CryptoPixError):
    """Raised when an invalid smart key is provided."""
    pass


class UnsupportedFormatError(CryptoPixError):
    """Raised when an unsupported file format is encountered."""
    pass


class MappingError(CryptoPixError):
    """Raised when color mapping operations fail."""
    pass


class SecurityError(CryptoPixError):
    """Raised when security validation fails."""
    pass