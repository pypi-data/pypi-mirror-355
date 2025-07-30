#!/usr/bin/env python3
"""
Test script to verify CryptoPix library functionality
"""

import sys
import os
from PIL import Image

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cryptopix import CryptoPix, encrypt_text, decrypt_image, __version__


def test_basic_functionality():
    """Test basic encryption and decryption"""
    print(f"Testing CryptoPix v{__version__}")
    print("=" * 50)
    
    # Test 1: Basic CryptoPix class usage
    print("Test 1: Basic CryptoPix class usage")
    cp = CryptoPix()
    text = "Hello, CryptoPix Library! 🔐"
    password = "test_password_123"
    
    try:
        # Encrypt
        print(f"Encrypting: '{text}'")
        image_data, smart_key = cp.encrypt(text, password)
        print(f"✓ Encryption successful")
        print(f"  Smart key: {smart_key[:50]}...")
        print(f"  Image size: {len(image_data.getvalue())} bytes")
        
        # Decrypt
        image = Image.open(image_data)
        print(f"  Image dimensions: {image.size[0]}x{image.size[1]}")
        
        result = cp.decrypt(image, smart_key, password)
        print(f"✓ Decryption successful")
        print(f"  Decrypted: '{result['content']}'")
        print(f"  Content type: {result['type']}")
        
        # Verify
        if result['content'] == text:
            print("✓ Content verification successful")
        else:
            print("✗ Content verification failed")
            return False
            
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        return False
    
    print()
    
    # Test 2: Convenience functions
    print("Test 2: Convenience functions")
    try:
        text2 = "Testing convenience functions"
        password2 = "another_password"
        
        # Encrypt using convenience function
        image_data2, smart_key2 = encrypt_text(text2, password2)
        print("✓ encrypt_text() successful")
        
        # Decrypt using convenience function
        image2 = Image.open(image_data2)
        result2 = decrypt_image(image2, smart_key2, password2)
        print("✓ decrypt_image() successful")
        
        if result2['content'] == text2:
            print("✓ Convenience functions verification successful")
        else:
            print("✗ Convenience functions verification failed")
            return False
            
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        return False
    
    print()
    
    # Test 3: Custom width
    print("Test 3: Custom width")
    try:
        custom_width = 25
        image_data3, smart_key3 = cp.encrypt("Custom width test", password, width=custom_width)
        image3 = Image.open(image_data3)
        
        if image3.size[0] == custom_width:
            print(f"✓ Custom width {custom_width} applied successfully")
        else:
            print(f"✗ Custom width failed: expected {custom_width}, got {image3.size[0]}")
            return False
            
        # Verify decryption still works
        result3 = cp.decrypt(image3, smart_key3, password)
        if result3['content'] == "Custom width test":
            print("✓ Custom width decryption successful")
        else:
            print("✗ Custom width decryption failed")
            return False
            
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
        return False
    
    print()
    
    # Test 4: Error handling
    print("Test 4: Error handling")
    try:
        from cryptopix.core.exceptions import InvalidPasswordError, InvalidKeyError
        
        # Test wrong password
        try:
            cp.decrypt(image, smart_key, "wrong_password")
            print("✗ Should have raised InvalidPasswordError")
            return False
        except (InvalidPasswordError, Exception) as e:
            if "password" in str(e).lower() or "authentication" in str(e).lower():
                print("✓ Password error correctly raised for wrong password")
            else:
                print(f"✓ Exception raised for wrong password: {type(e).__name__}")
        
        # Test invalid key
        try:
            cp.decrypt(image, "invalid_key", password)
            print("✗ Should have raised InvalidKeyError")
            return False
        except (InvalidKeyError, Exception) as e:
            if "key" in str(e).lower() or "invalid" in str(e).lower():
                print("✓ Key error correctly raised for invalid key")
            else:
                print(f"✓ Exception raised for invalid key: {type(e).__name__}")
            
    except Exception as e:
        print(f"✗ Test 4 failed: {e}")
        return False
    
    print()
    print("🎉 All tests passed successfully!")
    return True


def test_performance():
    """Test performance with different text sizes"""
    import time
    
    print("Performance Tests")
    print("=" * 50)
    
    cp = CryptoPix()
    password = "perf_test"
    
    test_cases = [
        ("Small (50 chars)", "A" * 50),
        ("Medium (500 chars)", "B" * 500),
        ("Large (5000 chars)", "C" * 5000),
    ]
    
    for description, text in test_cases:
        try:
            # Encryption timing
            start_time = time.time()
            image_data, smart_key = cp.encrypt(text, password)
            encrypt_time = time.time() - start_time
            
            # Decryption timing
            image = Image.open(image_data)
            start_time = time.time()
            result = cp.decrypt(image, smart_key, password)
            decrypt_time = time.time() - start_time
            
            # Verify correctness
            if result['content'] == text:
                print(f"{description}:")
                print(f"  Encryption: {encrypt_time:.3f}s")
                print(f"  Decryption: {decrypt_time:.3f}s")
                print(f"  Image size: {len(image_data.getvalue())} bytes")
                print(f"  Dimensions: {image.size[0]}x{image.size[1]}")
            else:
                print(f"✗ {description} failed verification")
                
        except Exception as e:
            print(f"✗ {description} failed: {e}")
    
    print()


if __name__ == "__main__":
    print("CryptoPix Library Test Suite")
    print("=" * 60)
    print()
    
    # Run functionality tests
    if test_basic_functionality():
        print()
        # Run performance tests
        test_performance()
        
        print("Library verification complete! ✅")
        print()
        print("The CryptoPix library is ready for packaging and publishing.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)