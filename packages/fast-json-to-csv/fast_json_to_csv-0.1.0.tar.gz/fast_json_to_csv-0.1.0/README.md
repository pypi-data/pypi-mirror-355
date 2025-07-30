# Fast JSON to CSV

Minimal dependencies fast and efficient JSON to CSV converter that doesn't rely on the standard CSV module. This package provides a simple way to convert JSON data to CSV format with support for nested JSON structures.

## Features

- Convert JSON data to CSV format
- Handle nested JSON structures
- No dependency on Python's CSV module
- Support for custom delimiters
- Efficient memory usage

## Installation

```bash
pip install fast-json-to-csv
```

## Usage

```python
from fast_json_to_csv import JsonToCSV

# Your JSON data
json_data = {
    "name": "John",
    "address": {
        "city": "New York",
        "zip": "10001"
    }
}

# Convert to CSV
converter = JsonToCSV(json_data)
headers, body = converter.json_to_csv()

# Write to file
with open('output.csv', 'w') as f:
    # Write headers
    f.write(', '.join(headers))
    f.write('\n')
    # Write body
    for row in body:
        f.write(', '.join(row))
        f.write('\n')
```

## API Reference

### JsonToCSV

The main class for converting JSON to CSV.

#### Methods

- `json_to_csv()`: Converts the JSON data to CSV format, returns a tuple of (headers, body)
- `flatten(d, prefix)`: Static method to flatten nested JSON structures
- `merge_d(a, b)`: Static method to merge dictionaries

## License

This project is licensed under the MIT License - see the LICENSE file for details. 