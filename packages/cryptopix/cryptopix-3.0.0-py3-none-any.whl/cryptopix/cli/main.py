"""
CryptoPix Command Line Interface

This module provides a command-line interface for the CryptoPix library,
allowing users to encrypt and decrypt files from the terminal.
"""

import sys
import os
import argparse
from pathlib import Path
from PIL import Image
import getpass

# Add the parent directory to the path so we can import cryptopix
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from cryptopix import CryptoPix, __version__
from cryptopix.core.exceptions import CryptoPixError


def setup_parser():
    """Set up command-line argument parser"""
    parser = argparse.ArgumentParser(
        description='CryptoPix - Secure text-to-image encryption tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Encrypt text to image
  cryptopix encrypt -t "Hello World" -p mypassword -o encrypted.webp
  
  # Encrypt file contents to image
  cryptopix encrypt -f input.txt -p mypassword -o encrypted.webp
  
  # Decrypt image to text
  cryptopix decrypt -i encrypted.webp -k "cryptopix_v2:..." -p mypassword
  
  # Decrypt image and save to file
  cryptopix decrypt -i encrypted.webp -k "cryptopix_v2:..." -p mypassword -o decrypted.txt
        """
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'CryptoPix {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Encrypt command
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt text to image')
    encrypt_group = encrypt_parser.add_mutually_exclusive_group(required=True)
    encrypt_group.add_argument('-t', '--text', help='Text to encrypt')
    encrypt_group.add_argument('-f', '--file', help='File containing text to encrypt')
    
    encrypt_parser.add_argument('-p', '--password', help='Password for encryption (will prompt if not provided)')
    encrypt_parser.add_argument('-o', '--output', required=True, help='Output image file path')
    encrypt_parser.add_argument('-w', '--width', type=int, help='Image width (auto-calculated if not provided)')
    encrypt_parser.add_argument('--key-output', help='File to save the smart key')
    
    # Decrypt command
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt image to text')
    decrypt_parser.add_argument('-i', '--image', required=True, help='Input image file path')
    decrypt_parser.add_argument('-k', '--key', help='Smart key (will prompt if not provided)')
    decrypt_parser.add_argument('--key-file', help='File containing the smart key')
    decrypt_parser.add_argument('-p', '--password', help='Password for decryption (will prompt if not provided)')
    decrypt_parser.add_argument('-o', '--output', help='Output text file (prints to stdout if not provided)')
    
    return parser


def get_password(prompt="Password: "):
    """Securely get password from user"""
    return getpass.getpass(prompt)


def read_file(file_path):
    """Read file contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def write_file(file_path, content, mode='w'):
    """Write content to file"""
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def encrypt_command(args):
    """Handle encrypt command"""
    # Get text to encrypt
    if args.text:
        text = args.text
    else:
        text = read_file(args.file)
    
    # Get password
    password = args.password
    if not password:
        password = get_password("Enter encryption password: ")
    
    if not password:
        print("Password cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize CryptoPix
        cp = CryptoPix()
        
        # Encrypt text
        print("Encrypting text to image...")
        image_data, smart_key = cp.encrypt(text, password, args.width)
        
        # Save image
        output_path = Path(args.output)
        with open(output_path, 'wb') as f:
            f.write(image_data.getvalue())
        
        print(f"✓ Encrypted image saved to: {output_path}")
        print(f"✓ Smart key: {smart_key}")
        
        # Save smart key to file if requested
        if args.key_output:
            write_file(args.key_output, smart_key)
            print(f"✓ Smart key saved to: {args.key_output}")
        
        # Show statistics
        image_size = len(image_data.getvalue())
        text_size = len(text.encode('utf-8'))
        compression_ratio = image_size / text_size if text_size > 0 else 0
        
        print(f"\nStatistics:")
        print(f"  Original text size: {text_size} bytes")
        print(f"  Encrypted image size: {image_size} bytes")
        print(f"  Compression ratio: {compression_ratio:.2f}x")
        
    except CryptoPixError as e:
        print(f"Encryption error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def decrypt_command(args):
    """Handle decrypt command"""
    # Get smart key
    smart_key = args.key
    if not smart_key and args.key_file:
        smart_key = read_file(args.key_file).strip()
    
    if not smart_key:
        smart_key = input("Enter smart key: ").strip()
    
    if not smart_key:
        print("Smart key cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    # Get password
    password = args.password
    if not password:
        password = get_password("Enter decryption password: ")
    
    if not password:
        print("Password cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load image
        print("Loading encrypted image...")
        image = Image.open(args.image)
        
        # Initialize CryptoPix
        cp = CryptoPix()
        
        # Decrypt image
        print("Decrypting image to text...")
        result = cp.decrypt(image, smart_key, password)
        
        if not result.get('success', False):
            print("Decryption failed", file=sys.stderr)
            sys.exit(1)
        
        decrypted_content = result['content']
        content_type = result['type']
        
        # Output result
        if args.output:
            if content_type == 'binary':
                # Save binary data as base64
                write_file(args.output, decrypted_content)
                print(f"✓ Decrypted binary data (base64) saved to: {args.output}")
            else:
                # Save text data
                write_file(args.output, decrypted_content)
                print(f"✓ Decrypted text saved to: {args.output}")
        else:
            if content_type == 'binary':
                print("Decrypted content (base64 encoded binary data):")
                print(decrypted_content)
            else:
                print("Decrypted text:")
                print(decrypted_content)
        
        # Show statistics
        print(f"\nStatistics:")
        print(f"  Content type: {content_type}")
        print(f"  Decrypted size: {len(decrypted_content)} characters")
        print(f"  Image size: {image.size[0]}x{image.size[1]} pixels")
        
    except CryptoPixError as e:
        print(f"Decryption error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'encrypt':
        encrypt_command(args)
    elif args.command == 'decrypt':
        decrypt_command(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()