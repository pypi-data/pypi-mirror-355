"""
Color Mapping Module

This module provides efficient color mapping utilities for the CryptoPix library.
It includes an LRU cache for performance optimization and supports various
mapping backends.
"""

import sqlite3
import csv
import os
import threading
from collections import OrderedDict
from typing import Optional, Dict, Tuple
import logging

from .exceptions import MappingError

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, capacity: int = 10000):
        """
        Initialize LRU cache with specified capacity
        
        Args:
            capacity: Maximum number of items to cache
        """
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key, default=None):
        """
        Get value from cache, moving item to end (most recently used)
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        with self.lock:
            if key in self.cache:
                # Move to end (mark as recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                return default
    
    def put(self, key, value):
        """
        Put value in cache, removing oldest if at capacity
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.pop(key)
                self.cache[key] = value
            else:
                # Add new key
                if len(self.cache) >= self.capacity:
                    # Remove oldest item
                    self.cache.popitem(last=False)
                self.cache[key] = value
    
    def clear(self):
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def __len__(self):
        """Return number of cached entries"""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self):
        """Return cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'size': len(self.cache),
                'capacity': self.capacity
            }


class ColorMapper:
    """
    Efficient color mapping system with LRU caching and SQLite backend
    """
    
    def __init__(self, mapping_file: Optional[str] = None, cache_size: int = 10000):
        """
        Initialize color mapper
        
        Args:
            mapping_file: Path to CSV mapping file (optional)
            cache_size: Size of LRU cache
        """
        self.cache = LRUCache(cache_size)
        self.db_path = None
        self.db_connection = None
        self.lock = threading.RLock()
        
        if mapping_file and os.path.exists(mapping_file):
            self.initialize_from_file(mapping_file)
    
    def initialize_from_file(self, mapping_file: str):
        """
        Initialize mappings from CSV file
        
        Args:
            mapping_file: Path to CSV mapping file
            
        Raises:
            MappingError: If file loading fails
        """
        try:
            # Create in-memory SQLite database
            self.db_path = ":memory:"
            self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Create mapping table
            cursor = self.db_connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS color_mappings (
                    binary_value TEXT PRIMARY KEY,
                    hex_color TEXT NOT NULL
                )
            ''')
            
            # Create reverse lookup index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hex_color 
                ON color_mappings(hex_color)
            ''')
            
            # Load mappings from CSV
            self._load_csv_mappings(mapping_file)
            
            # Preload common mappings into cache
            self._preload_common_mappings()
            
            logger.info(f"Color mapper initialized with {self._get_total_count()} mappings")
            
        except Exception as e:
            raise MappingError(f"Failed to initialize color mapper: {str(e)}")
    
    def _load_csv_mappings(self, mapping_file: str):
        """Load mappings from CSV file into database"""
        cursor = self.db_connection.cursor()
        batch_size = 1000
        batch = []
        
        with open(mapping_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header if present
            first_row = next(reader, None)
            if first_row and not (first_row[0].startswith('0') or first_row[0].startswith('1')):
                pass  # Skip header row
            else:
                # Process first row as data
                if first_row:
                    batch.append(tuple(first_row))
            
            # Process remaining rows
            for row in reader:
                if len(row) >= 2:
                    batch.append((row[0], row[1]))
                    
                    if len(batch) >= batch_size:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO color_mappings (binary_value, hex_color) VALUES (?, ?)',
                            batch
                        )
                        batch = []
            
            # Insert remaining batch
            if batch:
                cursor.executemany(
                    'INSERT OR REPLACE INTO color_mappings (binary_value, hex_color) VALUES (?, ?)',
                    batch
                )
        
        self.db_connection.commit()
    
    def _preload_common_mappings(self, limit: int = 1000):
        """Preload most common mappings into cache"""
        if not self.db_connection:
            return
            
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT binary_value, hex_color FROM color_mappings LIMIT ?', (limit,))
        
        for binary_value, hex_color in cursor.fetchall():
            self.cache.put(f"b2c_{binary_value}", hex_color)
            self.cache.put(f"c2b_{hex_color}", binary_value)
    
    def _get_total_count(self) -> int:
        """Get total number of mappings in database"""
        if not self.db_connection:
            return 0
            
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM color_mappings')
        return cursor.fetchone()[0]
    
    def get_color_for_binary(self, binary_value: str, default_color: str = "#000000") -> str:
        """
        Get hex color for binary value
        
        Args:
            binary_value: Binary string to look up
            default_color: Default color if not found
            
        Returns:
            Hex color code
        """
        cache_key = f"b2c_{binary_value}"
        
        # Check cache first
        color = self.cache.get(cache_key)
        if color is not None:
            return color
        
        # Check database
        if self.db_connection:
            with self.lock:
                cursor = self.db_connection.cursor()
                cursor.execute('SELECT hex_color FROM color_mappings WHERE binary_value = ?', (binary_value,))
                result = cursor.fetchone()
                
                if result:
                    color = result[0]
                    self.cache.put(cache_key, color)
                    return color
        
        # Return default and cache it
        self.cache.put(cache_key, default_color)
        return default_color
    
    def get_binary_for_color(self, hex_color: str, default_binary: Optional[str] = None) -> Optional[str]:
        """
        Get binary value for hex color
        
        Args:
            hex_color: Hex color to look up
            default_binary: Default binary if not found
            
        Returns:
            Binary string or None
        """
        cache_key = f"c2b_{hex_color}"
        
        # Check cache first
        binary = self.cache.get(cache_key)
        if binary is not None:
            return binary
        
        # Check database
        if self.db_connection:
            with self.lock:
                cursor = self.db_connection.cursor()
                cursor.execute('SELECT binary_value FROM color_mappings WHERE hex_color = ?', (hex_color,))
                result = cursor.fetchone()
                
                if result:
                    binary = result[0]
                    self.cache.put(cache_key, binary)
                    return binary
        
        # Return default and cache it if provided
        if default_binary is not None:
            self.cache.put(cache_key, default_binary)
        
        return default_binary
    
    def add_mapping(self, binary_value: str, hex_color: str):
        """
        Add new mapping to database and cache
        
        Args:
            binary_value: Binary string
            hex_color: Hex color code
        """
        if self.db_connection:
            with self.lock:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO color_mappings (binary_value, hex_color) VALUES (?, ?)',
                    (binary_value, hex_color)
                )
                self.db_connection.commit()
                
                # Update cache
                self.cache.put(f"b2c_{binary_value}", hex_color)
                self.cache.put(f"c2b_{hex_color}", binary_value)
    
    def get_stats(self) -> Dict:
        """Get mapping statistics"""
        cache_stats = self.cache.get_stats()
        total_mappings = self._get_total_count()
        
        return {
            'total_mappings': total_mappings,
            'cache_stats': cache_stats,
            'database_path': self.db_path or "Not initialized"
        }
    
    def cleanup(self):
        """Clean up database connections"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
        self.cache.clear()


# Global color mapper instance (optional)
_global_mapper = None


def get_global_mapper() -> Optional[ColorMapper]:
    """Get the global color mapper instance"""
    return _global_mapper


def initialize_global_mapper(mapping_file: Optional[str] = None, cache_size: int = 10000):
    """
    Initialize global color mapper
    
    Args:
        mapping_file: Path to CSV mapping file
        cache_size: Size of LRU cache
    """
    global _global_mapper
    _global_mapper = ColorMapper(mapping_file, cache_size)


def cleanup_global_mapper():
    """Clean up global color mapper"""
    global _global_mapper
    if _global_mapper:
        _global_mapper.cleanup()
        _global_mapper = None