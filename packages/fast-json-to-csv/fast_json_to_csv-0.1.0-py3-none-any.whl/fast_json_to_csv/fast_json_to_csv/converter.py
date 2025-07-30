"""
Core functionality for fast JSON to CSV conversion.
This is a custom implementation of the JsonToCSV class that provides a faster way to convert JSON data to CSV format.
@author: mariyasnow
@date: 2025-06
@version: 0.1.0
@license: MIT
@website: https://github.com/mariyasnow/fast_json_to_csv
"""

import json
import urllib.request
from typing import Dict, List, Tuple, Any, Union

class JsonToCSV:
    """
    A class for converting JSON data to CSV format.
    
    This class provides methods to convert JSON data to CSV format without
    relying on the standard CSV module. It handles nested JSON structures
    and provides efficient conversion.
    """
    
    def __init__(self, json_d: Union[Dict, List]):
        """
        Initialize the converter with JSON data.
        
        Args:
            json_d: The JSON data to convert (dict or list)
        """
        self.d = json_d

    def json_to_csv(self) -> Tuple[List[str], List[List[str]]]:
        """
        Convert the JSON data to CSV format.
        
        Returns:
            A tuple containing:
            - List of header names
            - List of rows (each row is a list of values)
        """
        flatD = self.flatten(self.d, '')
        headers = list(flatD.keys())
        body_t = flatD.values()
        body = [list(x) for x in zip(*body_t) if len(''.join(str(x))) != 0]
        return headers, body

    @staticmethod
    def flatten(d: Union[Dict, List], prefix: str) -> Dict[str, List]:
        """
        Flatten a nested JSON structure into a dictionary with lists of values.
        
        Args:
            d: The JSON data to flatten
            prefix: The prefix for nested keys
            
        Returns:
            A flattened dictionary with lists of values
        """
        if len(d) == 0:
            return {}
        
        res = {}
        delim = '__' if prefix else ''

        if isinstance(d, list):
            for v in d:
                res = JsonToCSV.merge_d(res, JsonToCSV.flatten(v, prefix))
        else:
            for k, v in d.items():
                nk = f'{prefix}{delim}{k}'
                if not isinstance(v, dict):
                    if nk in res:
                        res[nk].append(v)
                    else:
                        res[nk] = [v]
                else:
                    res = JsonToCSV.merge_d(res, JsonToCSV.flatten(v, nk))
        return res

    @staticmethod
    def merge_d(a: Dict[str, List], b: Dict[str, List]) -> Dict[str, List]:
        """
        Merge two dictionaries of lists.
        
        Args:
            a: First dictionary
            b: Second dictionary
            
        Returns:
            Merged dictionary
        """
        for k, v in b.items():
            if k in a:
                a[k].extend(v)
            else:
                a[k] = v
        return a

def write_to_file_csv(filename: str, headers: List[str], body: List[List[str]]) -> None:
    """
    Write data to a CSV file.
    
    Args:
        filename: Path to the output file
        headers: List of column headers
        body: List of rows (each row is a list of values)
    """
    with open(filename, 'w') as f:
        f.write(', '.join(headers))
        f.write('\n')
        for ln in body:
            f.write(', '.join(str(x) for x in ln))
            f.write('\n')

def write_to_file_json(filename: str, data: Union[Dict, List]) -> None:
    """
    Write data to a JSON file.
    
    Args:
        filename: Path to the output file
        data: The data to write
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def read_json(url: str) -> Union[Dict, List]:
    """
    Read JSON data from a URL.
    
    Args:
        url: URL to fetch JSON data from
        
    Returns:
        The parsed JSON data
    """
    with urllib.request.urlopen(url) as f:
        return json.loads(f.read().decode(f.info().get_param('charset') or 'utf-8')) 