"""
Fast JSON to CSV converter.

This package provides a fast and efficient way to convert JSON data to CSV format
without relying on the standard CSV module.
"""

from .converter import JsonToCSV, write_to_file_csv, write_to_file_json, read_json

__version__ = "0.1.0"
__all__ = ['JsonToCSV', 'write_to_file_csv', 'write_to_file_json', 'read_json'] 