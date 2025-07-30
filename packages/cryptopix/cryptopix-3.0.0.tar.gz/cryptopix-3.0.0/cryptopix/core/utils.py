"""
Utility functions for CryptoPix library
"""

import os
import base64
import hashlib
import secrets
from typing import Union, Optional, Tuple
from PIL import Image
from io import BytesIO

from .exceptions import UnsupportedFormatError, CryptoPixError


def validate_image_format(image_data: Union[bytes, BytesIO, Image.Image]) -> Image.Image:
    """
    Validate and convert image data to PIL Image
    
    Args:
        image_data: Image data in various formats
        
    Returns:
        PIL Image object
        
    Raises:
        UnsupportedFormatError: If image format is not supported
    """
    try:
        if isinstance(image_data, Image.Image):
            return image_data
        elif isinstance(image_data, bytes):
            return Image.open(BytesIO(image_data))
        elif isinstance(image_data, BytesIO):
            return Image.open(image_data)
        else:
            raise UnsupportedFormatError(f"Unsupported image format: {type(image_data)}")
    except Exception as e:
        raise UnsupportedFormatError(f"Failed to load image: {str(e)}")


def generate_secure_salt(length: int = 16) -> bytes:
    """
    Generate cryptographically secure random salt
    
    Args:
        length: Length of salt in bytes
        
    Returns:
        Random salt bytes
    """
    return secrets.token_bytes(length)


def calculate_optimal_dimensions(pixel_count: int, max_width: Optional[int] = None) -> Tuple[int, int]:
    """
    Calculate optimal image dimensions for given pixel count
    
    Args:
        pixel_count: Number of pixels needed
        max_width: Maximum width constraint
        
    Returns:
        Tuple of (width, height)
    """
    if pixel_count <= 0:
        return (1, 1)
    
    if pixel_count <= 100:
        # For small data, use a single row
        width = pixel_count
        height = 1
    else:
        # For larger data, create a square-ish image
        width = int(pixel_count ** 0.5) + 1
        height = (pixel_count + width - 1) // width
    
    # Apply width constraint if specified
    if max_width and width > max_width:
        width = max_width
        height = (pixel_count + width - 1) // width
    
    return (max(1, width), max(1, height))


def encode_binary_string(text: str) -> str:
    """
    Convert text to binary string representation
    
    Args:
        text: Text to convert
        
    Returns:
        Binary string representation
    """
    text_bytes = text.encode('utf-8')
    return ''.join(format(byte, '08b') for byte in text_bytes)


def decode_binary_string(binary_string: str) -> str:
    """
    Convert binary string back to text
    
    Args:
        binary_string: Binary string to convert
        
    Returns:
        Decoded text
        
    Raises:
        CryptoPixError: If decoding fails
    """
    try:
        text_bytes = bytearray()
        for i in range(0, len(binary_string), 8):
            byte_str = binary_string[i:i+8]
            if len(byte_str) == 8:
                text_bytes.append(int(byte_str, 2))
        
        return text_bytes.decode('utf-8')
    except Exception as e:
        raise CryptoPixError(f"Failed to decode binary string: {str(e)}")


def chunk_binary_string(binary_string: str, chunk_size: int = 24) -> Tuple[list, int]:
    """
    Split binary string into chunks of specified size with padding
    
    Args:
        binary_string: Binary string to chunk
        chunk_size: Size of each chunk
        
    Returns:
        Tuple of (chunks list, padding amount)
    """
    chunks = []
    padding = 0
    
    for i in range(0, len(binary_string), chunk_size):
        chunk = binary_string[i:i + chunk_size]
        if len(chunk) < chunk_size:
            padding = chunk_size - len(chunk)
            chunk = chunk.ljust(chunk_size, '0')
        chunks.append(chunk)
    
    return chunks, padding


def save_image_to_bytes(image: Image.Image, format: str = 'WEBP', **kwargs) -> BytesIO:
    """
    Save PIL Image to BytesIO buffer
    
    Args:
        image: PIL Image object
        format: Image format (WEBP, PNG, JPEG, etc.)
        **kwargs: Additional parameters for image saving
        
    Returns:
        BytesIO buffer containing image data
    """
    img_bytes = BytesIO()
    
    # Set default parameters for lossless compression
    if format.upper() == 'WEBP':
        kwargs.setdefault('lossless', True)
        kwargs.setdefault('quality', 100)
    elif format.upper() == 'PNG':
        kwargs.setdefault('optimize', True)
    
    image.save(img_bytes, format=format, **kwargs)
    img_bytes.seek(0)
    return img_bytes


def verify_smart_key_format(smart_key: str) -> bool:
    """
    Verify if smart key has valid CryptoPix format
    
    Args:
        smart_key: Smart key string to verify
        
    Returns:
        True if format is valid, False otherwise
    """
    if not smart_key or not isinstance(smart_key, str):
        return False
    
    if not smart_key.startswith('cryptopix_v2:'):
        return False
    
    parts = smart_key.split(':', 2)
    if len(parts) != 3:
        return False
    
    try:
        # Verify salt can be base64 decoded
        base64.b64decode(parts[1])
        # Verify metadata can be base64 decoded
        base64.b64decode(parts[2])
        return True
    except Exception:
        return False


def create_checksum(data: Union[str, bytes]) -> str:
    """
    Create SHA-256 checksum of data
    
    Args:
        data: Data to checksum
        
    Returns:
        Hex digest of checksum
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    return hashlib.sha256(data).hexdigest()


def secure_compare(a: str, b: str) -> bool:
    """
    Timing-safe string comparison
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename to extract extension from
        
    Returns:
        File extension (without dot)
    """
    return os.path.splitext(filename)[1][1:].lower()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    return f"{size:.1f} {size_names[size_index]}"