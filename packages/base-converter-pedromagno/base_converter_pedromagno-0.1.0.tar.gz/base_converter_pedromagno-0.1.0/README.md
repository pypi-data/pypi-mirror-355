# base_converter

A simple and reliable Python library for converting numbers between different bases (from base 2 to base 16), including support for fractions.

##Features

- Convert from any base (2 to 16) to decimal
- Convert from decimal to any base (2 to 16)
- Supports fractional numbers and negative values

## Installation

```bash
pip install .
```

## Usage

```python
from converter_base import convert_from_base_n_to_decimal, convert_from_decimal_to_base_n

print(convert_from_base_n_to_decimal("1A.4", 16)) # Output: 26.25
print(convert_from_decimal_to_base_n(26.25, 16)) # Output: '1A.4'
```


This project itself does not require any third-party libraries to use the core functionality.