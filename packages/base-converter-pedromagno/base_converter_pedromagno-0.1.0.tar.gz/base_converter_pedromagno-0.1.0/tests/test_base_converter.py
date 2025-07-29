import pytest

from base_converter.base_converter import (
    convert_from_base_n_to_decimal,
    convert_from_decimal_to_base_n
)

def test_convert_from_base_n_to_decimal_integer():
    assert convert_from_base_n_to_decimal("101", 2) == 5
    assert convert_from_base_n_to_decimal("7D", 16) == 125
    assert convert_from_base_n_to_decimal("325", 6) == 125

def test_convert_from_base_n_to_decimal_fraction():
    assert convert_from_base_n_to_decimal("1A.4", 16) == 26.25
    assert convert_from_base_n_to_decimal("101.01", 2) == 5.25
    assert convert_from_base_n_to_decimal("11.10", 4) == 5.25

def test_convert_from_decimal_to_base_n_integer():
    assert convert_from_decimal_to_base_n(5, 2, decimal_places=0) == "101"
    assert convert_from_decimal_to_base_n(125, 16, decimal_places=0) == "7D"
    assert convert_from_decimal_to_base_n(125, 6, decimal_places=0) == "325"

def test_convert_from_decimal_to_base_n_fraction():
    assert convert_from_decimal_to_base_n(26.25, 16, decimal_places=1) == "1A.4"
    assert convert_from_decimal_to_base_n(5.25, 2, decimal_places=2) == "101.01"
    assert convert_from_decimal_to_base_n(5.25, 4, decimal_places=2) == "11.10"

def test_negative_values():
    assert convert_from_base_n_to_decimal("-101", 2) == -5
    assert convert_from_decimal_to_base_n(-5.25, 2, decimal_places=2) == "-101.01"

def test_invalid_characters():
    with pytest.raises(ValueError):
        convert_from_base_n_to_decimal("1G", 16)
    with pytest.raises(ValueError):
        convert_from_base_n_to_decimal("129", 8)

def test_invalid_base():
    with pytest.raises(ValueError):
        convert_from_base_n_to_decimal("101", 1)
    with pytest.raises(ValueError):
        convert_from_decimal_to_base_n(10, 20)
