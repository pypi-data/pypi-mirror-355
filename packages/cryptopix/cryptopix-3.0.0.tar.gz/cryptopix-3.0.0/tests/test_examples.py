"""
Example usage tests for CryptoPix library

These tests serve as documentation examples and ensure
the example code in README works correctly.
"""

import pytest
import io
from PIL import Image
from cryptopix import CryptoPix, encrypt_text, decrypt_image


class TestREADMEExamples:
    """Test examples from README.md to ensure they work"""
    
    def test_basic_usage_example(self):
        """Test the basic usage example from README"""
        # Initialize
        cp = CryptoPix()
        
        # Encrypt text to image
        image_data, smart_key = cp.encrypt("Hello, World!", "my_password")
        
        # Save encrypted image (simulate file save)
        image_bytes = image_data.getvalue()
        assert len(image_bytes) > 0
        
        # Load image and decrypt
        image = Image.open(io.BytesIO(image_bytes))
        result = cp.decrypt(image, smart_key, "my_password")
        
        assert result['content'] == "Hello, World!"
    
    def test_convenience_functions_example(self):
        """Test convenience functions example from README"""
        # Quick encryption
        image_data, smart_key = encrypt_text("Secret message", "password123")
        
        # Quick decryption
        image = Image.open(image_data)
        result = decrypt_image(image, smart_key, "password123")
        
        assert result['content'] == "Secret message"
    
    def test_custom_width_example(self):
        """Test custom width example from README"""
        cp = CryptoPix()
        
        # Specify custom width
        image_data, smart_key = cp.encrypt("Long text content", "password", width=100)
        
        # Verify width
        image = Image.open(image_data)
        assert image.size[0] == 100
        
        # Verify decryption
        result = cp.decrypt(image, smart_key, "password")
        assert result['content'] == "Long text content"
    
    def test_error_handling_example(self):
        """Test error handling example from README"""
        from cryptopix.core.exceptions import (
            EncryptionError, 
            DecryptionError, 
            InvalidPasswordError
        )
        
        cp = CryptoPix()
        
        # Test encryption error (empty text)
        try:
            image_data, smart_key = cp.encrypt("", "password")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        # Test invalid password error
        image_data, smart_key = cp.encrypt("test", "password")
        image = Image.open(image_data)
        
        try:
            result = cp.decrypt(image, smart_key, "wrong_password")
            assert False, "Should have raised InvalidPasswordError"
        except InvalidPasswordError:
            pass  # Expected
    
    def test_binary_data_handling(self):
        """Test binary data handling example"""
        import base64
        
        cp = CryptoPix()
        
        # Create some binary-like data (will be treated as text by our current implementation)
        # In a real scenario, binary data would need special handling
        text_data = "Binary-like content with special chars: \x00\x01\x02"
        
        image_data, smart_key = cp.encrypt(text_data, "password")
        image = Image.open(image_data)
        result = cp.decrypt(image, smart_key, "password")
        
        # Should successfully decrypt
        assert result['success'] is True
        assert result['content'] == text_data


class TestPerformanceExamples:
    """Test performance characteristics mentioned in README"""
    
    def test_small_text_performance(self):
        """Test encryption/decryption of small text (< 100 chars)"""
        import time
        
        cp = CryptoPix()
        small_text = "Small text message for testing performance."
        
        # Measure encryption time
        start_time = time.time()
        image_data, smart_key = cp.encrypt(small_text, "password")
        encryption_time = time.time() - start_time
        
        # Measure decryption time
        image = Image.open(image_data)
        start_time = time.time()
        result = cp.decrypt(image, smart_key, "password")
        decryption_time = time.time() - start_time
        
        # Verify correctness
        assert result['content'] == small_text
        
        # Performance should be reasonable (very lenient for testing)
        assert encryption_time < 1.0  # Should be much faster, but being generous
        assert decryption_time < 1.0
    
    def test_medium_text_performance(self):
        """Test encryption/decryption of medium text (~1KB)"""
        import time
        
        cp = CryptoPix()
        medium_text = "A" * 1000  # 1KB of text
        
        start_time = time.time()
        image_data, smart_key = cp.encrypt(medium_text, "password")
        encryption_time = time.time() - start_time
        
        image = Image.open(image_data)
        start_time = time.time()
        result = cp.decrypt(image, smart_key, "password")
        decryption_time = time.time() - start_time
        
        assert result['content'] == medium_text
        assert encryption_time < 2.0  # Generous timing
        assert decryption_time < 2.0


class TestCompatibilityExamples:
    """Test compatibility with different Python versions and environments"""
    
    def test_cross_instance_compatibility(self):
        """Test that encrypted data from one instance can be decrypted by another"""
        cp1 = CryptoPix()
        cp2 = CryptoPix()
        
        text = "Cross-instance compatibility test"
        password = "shared_password"
        
        # Encrypt with first instance
        image_data, smart_key = cp1.encrypt(text, password)
        
        # Decrypt with second instance
        image = Image.open(image_data)
        result = cp2.decrypt(image, smart_key, password)
        
        assert result['content'] == text
    
    def test_image_format_compatibility(self):
        """Test that generated images are valid WebP format"""
        cp = CryptoPix()
        
        image_data, smart_key = cp.encrypt("Test message", "password")
        
        # Verify it's a valid image
        image = Image.open(image_data)
        assert image.format == 'WEBP'
        assert image.mode == 'RGB'
        
        # Verify it can be saved and reloaded
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='WEBP')
        output_buffer.seek(0)
        
        reloaded_image = Image.open(output_buffer)
        result = cp.decrypt(reloaded_image, smart_key, "password")
        assert result['content'] == "Test message"


if __name__ == "__main__":
    pytest.main([__file__])