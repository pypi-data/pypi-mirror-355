"""
Tests for CryptoPix encryption functionality
"""

import pytest
import io
from PIL import Image

from cryptopix import CryptoPix, encrypt_text, decrypt_image
from cryptopix.core.exceptions import (
    EncryptionError,
    DecryptionError,
    InvalidPasswordError,
    InvalidKeyError,
)


class TestCryptoPix:
    """Test cases for CryptoPix class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cp = CryptoPix()
        self.test_text = "Hello, World! This is a test message."
        self.test_password = "test_password_123"
    
    def test_basic_encryption_decryption(self):
        """Test basic encryption and decryption workflow"""
        # Encrypt
        image_data, smart_key = self.cp.encrypt(self.test_text, self.test_password)
        
        assert isinstance(image_data, io.BytesIO)
        assert isinstance(smart_key, str)
        assert smart_key.startswith("cryptopix_v2:")
        
        # Load image and decrypt
        image = Image.open(image_data)
        result = self.cp.decrypt(image, smart_key, self.test_password)
        
        assert result['success'] is True
        assert result['content'] == self.test_text
        assert result['type'] == 'text'
    
    def test_empty_text_encryption(self):
        """Test encryption with empty text"""
        with pytest.raises(ValueError, match="Text to encrypt cannot be empty"):
            self.cp.encrypt("", self.test_password)
    
    def test_empty_password_encryption(self):
        """Test encryption with empty password"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            self.cp.encrypt(self.test_text, "")
    
    def test_wrong_password_decryption(self):
        """Test decryption with wrong password"""
        image_data, smart_key = self.cp.encrypt(self.test_text, self.test_password)
        image = Image.open(image_data)
        
        with pytest.raises(InvalidPasswordError):
            self.cp.decrypt(image, smart_key, "wrong_password")
    
    def test_invalid_smart_key(self):
        """Test decryption with invalid smart key"""
        image_data, _ = self.cp.encrypt(self.test_text, self.test_password)
        image = Image.open(image_data)
        
        with pytest.raises(InvalidKeyError):
            self.cp.decrypt(image, "invalid_key", self.test_password)
    
    def test_malformed_smart_key(self):
        """Test decryption with malformed smart key"""
        image_data, _ = self.cp.encrypt(self.test_text, self.test_password)
        image = Image.open(image_data)
        
        with pytest.raises(InvalidKeyError):
            self.cp.decrypt(image, "cryptopix_v2:invalid", self.test_password)
    
    def test_custom_width(self):
        """Test encryption with custom width"""
        custom_width = 50
        image_data, smart_key = self.cp.encrypt(self.test_text, self.test_password, width=custom_width)
        
        image = Image.open(image_data)
        assert image.size[0] == custom_width
        
        # Verify decryption still works
        result = self.cp.decrypt(image, smart_key, self.test_password)
        assert result['content'] == self.test_text
    
    def test_long_text_encryption(self):
        """Test encryption with long text"""
        long_text = "A" * 10000  # 10KB of text
        
        image_data, smart_key = self.cp.encrypt(long_text, self.test_password)
        image = Image.open(image_data)
        result = self.cp.decrypt(image, smart_key, self.test_password)
        
        assert result['content'] == long_text
    
    def test_unicode_text(self):
        """Test encryption with Unicode characters"""
        unicode_text = "Hello 世界! 🌍 Testing émojis and spëcial chârs"
        
        image_data, smart_key = self.cp.encrypt(unicode_text, self.test_password)
        image = Image.open(image_data)
        result = self.cp.decrypt(image, smart_key, self.test_password)
        
        assert result['content'] == unicode_text
    
    def test_different_passwords_different_results(self):
        """Test that different passwords produce different encrypted results"""
        password1 = "password1"
        password2 = "password2"
        
        image_data1, smart_key1 = self.cp.encrypt(self.test_text, password1)
        image_data2, smart_key2 = self.cp.encrypt(self.test_text, password2)
        
        # Smart keys should be different
        assert smart_key1 != smart_key2
        
        # Images should be different
        assert image_data1.getvalue() != image_data2.getvalue()
    
    def test_same_text_different_encryptions(self):
        """Test that same text encrypted multiple times produces different results"""
        image_data1, smart_key1 = self.cp.encrypt(self.test_text, self.test_password)
        image_data2, smart_key2 = self.cp.encrypt(self.test_text, self.test_password)
        
        # Should be different due to random salt
        assert smart_key1 != smart_key2
        assert image_data1.getvalue() != image_data2.getvalue()
        
        # But both should decrypt to same text
        image1 = Image.open(image_data1)
        image2 = Image.open(image_data2)
        
        result1 = self.cp.decrypt(image1, smart_key1, self.test_password)
        result2 = self.cp.decrypt(image2, smart_key2, self.test_password)
        
        assert result1['content'] == self.test_text
        assert result2['content'] == self.test_text


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_encrypt_text_function(self):
        """Test encrypt_text convenience function"""
        text = "Test message"
        password = "test_pass"
        
        image_data, smart_key = encrypt_text(text, password)
        
        assert isinstance(image_data, io.BytesIO)
        assert smart_key.startswith("cryptopix_v2:")
    
    def test_decrypt_image_function(self):
        """Test decrypt_image convenience function"""
        text = "Test message"
        password = "test_pass"
        
        image_data, smart_key = encrypt_text(text, password)
        image = Image.open(image_data)
        
        result = decrypt_image(image, smart_key, password)
        
        assert result['content'] == text
        assert result['type'] == 'text'


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cp = CryptoPix()
    
    def test_empty_smart_key(self):
        """Test error handling for empty smart key"""
        # Create a dummy image
        dummy_image = Image.new('RGB', (10, 10))
        
        with pytest.raises(InvalidKeyError, match="Smart key cannot be empty"):
            self.cp.decrypt(dummy_image, "", "password")
    
    def test_empty_password_decryption(self):
        """Test error handling for empty password in decryption"""
        dummy_image = Image.new('RGB', (10, 10))
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            self.cp.decrypt(dummy_image, "dummy_key", "")


if __name__ == "__main__":
    pytest.main([__file__])