"""
Tests for the fast JSON to CSV converter.
"""

import unittest
from fast_json_to_csv import JsonToCSV, write_to_file_csv, write_to_file_json, read_json

class TestJsonToCSV(unittest.TestCase):
    """Test cases for the JSON to CSV converter."""

    def test_array_rotate(self):
        """Test array rotation functionality."""
        given_array = [10, 11, 14, 15]
        actual = array_rotate(given_array, 3)
        expected = [11, 14, 15, 10]
        self.assertEqual(actual, expected)

    def test_read_json(self):
        """Test reading JSON from URL."""
        d = read_json("http://mysafeinfo.com/api/data?list=englishmonarchs&format=json")
        actual = isinstance(d, list)
        expected = True
        self.assertEqual(actual, expected)

    def test_json_to_csv_conversion(self):
        """Test JSON to CSV conversion."""
        d = {'one': {'one': [1, 2, 3], 'two': 'one'}, 'kl': 'vp'}
        converter = JsonToCSV(d)
        actual = converter.json_to_csv()
        expected = (['one__two', 'one__one', 'kl'], [['', '', 'vp']])
        self.assertEqual(sorted(actual[0]), sorted(expected[0]))
        self.assertEqual(sorted(actual[1]), sorted(expected[1]))

    def test_flatten(self):
        """Test JSON flattening functionality."""
        d = {'one': {'one': [1, 2, 3], 'two': 'one'}, 'kl': 'vp'}
        prefix = ''
        converter = JsonToCSV(d)
        actual = converter.flatten(d, prefix)
        expected = {'kl': ['vp'], 'one__one': ['', '', [1, 2, 3]], 'one__two': ['', '', 'one']}
        self.assertEqual(actual, expected)

def array_rotate(arr, byn):
    """Rotate array elements by shift without using another array."""
    n = len(arr) % byn
    if n == 0 or n == len(arr):
        return arr
    return arr[n:] + arr[:n]

if __name__ == '__main__':
    unittest.main() 