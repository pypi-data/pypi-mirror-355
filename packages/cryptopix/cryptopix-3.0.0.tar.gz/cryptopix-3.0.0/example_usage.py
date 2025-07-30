#!/usr/bin/env python3
"""
CryptoPix Library Usage Examples

This file demonstrates various ways to use the CryptoPix library
for encrypting text into images and decrypting them back.
"""

import os
import sys
from PIL import Image

# Add the current directory to Python path for local testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cryptopix import CryptoPix, encrypt_text, decrypt_image


def example_1_basic_usage():
    """Example 1: Basic encryption and decryption"""
    print("=" * 60)
    print("Example 1: Basic Encryption and Decryption")
    print("=" * 60)
    
    # Initialize CryptoPix
    cp = CryptoPix()
    
    # Text to encrypt
    secret_message = "This is a secret message that will be hidden in an image!"
    password = "my_secure_password_123"
    
    print(f"Original message: {secret_message}")
    print(f"Password: {password}")
    
    # Encrypt text to image
    image_data, smart_key = cp.encrypt(secret_message, password)
    
    # Save the encrypted image
    with open("encrypted_message.webp", "wb") as f:
        f.write(image_data.getvalue())
    
    print(f"Smart key: {smart_key}")
    print("Encrypted image saved as: encrypted_message.webp")
    
    # Load and decrypt the image
    image = Image.open("encrypted_message.webp")
    result = cp.decrypt(image, smart_key, password)
    
    print(f"Decrypted message: {result['content']}")
    print(f"Content type: {result['type']}")
    
    # Verify the message
    if result['content'] == secret_message:
        print("✓ Encryption and decryption successful!")
    else:
        print("✗ Something went wrong!")
    
    print()


def example_2_convenience_functions():
    """Example 2: Using convenience functions"""
    print("=" * 60)
    print("Example 2: Convenience Functions")
    print("=" * 60)
    
    message = "Quick encryption using convenience functions"
    password = "simple_password"
    
    print(f"Message: {message}")
    
    # Quick encryption
    image_data, smart_key = encrypt_text(message, password)
    
    # Save image
    with open("quick_encrypted.webp", "wb") as f:
        f.write(image_data.getvalue())
    
    # Quick decryption
    image = Image.open("quick_encrypted.webp")
    result = decrypt_image(image, smart_key, password)
    
    print(f"Decrypted: {result['content']}")
    print("✓ Convenience functions work perfectly!")
    print()


def example_3_custom_dimensions():
    """Example 3: Custom image dimensions"""
    print("=" * 60)
    print("Example 3: Custom Image Dimensions")
    print("=" * 60)
    
    cp = CryptoPix()
    message = "Testing custom image dimensions"
    password = "dimension_test"
    
    # Test different widths
    for width in [10, 25, 50, 100]:
        image_data, smart_key = cp.encrypt(message, password, width=width)
        
        # Check the actual dimensions
        image = Image.open(image_data)
        print(f"Width {width}: Actual dimensions = {image.size[0]}x{image.size[1]}")
        
        # Verify decryption still works
        result = cp.decrypt(image, smart_key, password)
        assert result['content'] == message
    
    print("✓ Custom dimensions work correctly!")
    print()


def example_4_long_text():
    """Example 4: Handling long text"""
    print("=" * 60)
    print("Example 4: Long Text Encryption")
    print("=" * 60)
    
    cp = CryptoPix()
    
    # Create a long text (story or document)
    long_text = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis 
    nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore 
    eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt 
    in culpa qui officia deserunt mollit anim id est laborum.
    
    Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
    doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
    veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim 
    ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit.
    """ * 5  # Repeat 5 times to make it longer
    
    password = "long_text_password"
    
    print(f"Text length: {len(long_text)} characters")
    
    # Encrypt the long text
    image_data, smart_key = cp.encrypt(long_text, password)
    image = Image.open(image_data)
    
    print(f"Image dimensions: {image.size[0]}x{image.size[1]} pixels")
    print(f"Image file size: {len(image_data.getvalue())} bytes")
    
    # Decrypt and verify
    result = cp.decrypt(image, smart_key, password)
    
    if result['content'] == long_text:
        print("✓ Long text encryption/decryption successful!")
    else:
        print("✗ Long text test failed!")
    
    print()


def example_5_unicode_text():
    """Example 5: Unicode and special characters"""
    print("=" * 60)
    print("Example 5: Unicode and Special Characters")
    print("=" * 60)
    
    cp = CryptoPix()
    
    # Text with various Unicode characters
    unicode_text = """
    Hello World! 🌍
    こんにちは世界！ 
    Здравствуй мир! 
    مرحبا بالعالم!
    🔐 Encrypted with CryptoPix 🔐
    Special chars: @#$%^&*()_+-=[]{}|;:,.<>?
    """
    
    password = "unicode_test_🔑"
    
    print(f"Unicode text: {unicode_text.strip()}")
    
    # Encrypt
    image_data, smart_key = cp.encrypt(unicode_text, password)
    
    # Save
    with open("unicode_encrypted.webp", "wb") as f:
        f.write(image_data.getvalue())
    
    # Decrypt
    image = Image.open("unicode_encrypted.webp")
    result = cp.decrypt(image, smart_key, password)
    
    print(f"Decrypted: {result['content'].strip()}")
    
    if result['content'] == unicode_text:
        print("✓ Unicode text encryption successful!")
    else:
        print("✗ Unicode text test failed!")
    
    print()


def example_6_error_handling():
    """Example 6: Error handling demonstration"""
    print("=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)
    
    from cryptopix.core.exceptions import (
        EncryptionError, 
        DecryptionError, 
        InvalidPasswordError, 
        InvalidKeyError
    )
    
    cp = CryptoPix()
    
    # Create a valid encryption first
    message = "Test message for error handling"
    password = "correct_password"
    
    image_data, smart_key = cp.encrypt(message, password)
    image = Image.open(image_data)
    
    # Test 1: Wrong password
    print("Test 1: Wrong password")
    try:
        result = cp.decrypt(image, smart_key, "wrong_password")
        print("✗ Should have raised an exception")
    except Exception as e:
        print(f"✓ Correctly caught error: {type(e).__name__}")
    
    # Test 2: Invalid smart key
    print("Test 2: Invalid smart key")
    try:
        result = cp.decrypt(image, "invalid_key", password)
        print("✗ Should have raised an exception")
    except Exception as e:
        print(f"✓ Correctly caught error: {type(e).__name__}")
    
    # Test 3: Empty text encryption
    print("Test 3: Empty text")
    try:
        cp.encrypt("", password)
        print("✗ Should have raised an exception")
    except ValueError as e:
        print(f"✓ Correctly caught error: {type(e).__name__}")
    
    # Test 4: Empty password
    print("Test 4: Empty password")
    try:
        cp.encrypt(message, "")
        print("✗ Should have raised an exception")
    except ValueError as e:
        print(f"✓ Correctly caught error: {type(e).__name__}")
    
    print("✓ Error handling works correctly!")
    print()


def cleanup_files():
    """Clean up generated files"""
    files_to_remove = [
        "encrypted_message.webp",
        "quick_encrypted.webp", 
        "unicode_encrypted.webp"
    ]
    
    for filename in files_to_remove:
        try:
            os.remove(filename)
            print(f"Cleaned up: {filename}")
        except FileNotFoundError:
            pass


def main():
    """Run all examples"""
    print("CryptoPix Library Usage Examples")
    print("================================")
    print()
    
    try:
        example_1_basic_usage()
        example_2_convenience_functions()
        example_3_custom_dimensions()
        example_4_long_text()
        example_5_unicode_text()
        example_6_error_handling()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    finally:
        cleanup_files()


if __name__ == "__main__":
    main()