import string

DIGITS = string.digits + string.ascii_uppercase


def convert_from_base_n_to_decimal(value: str, base: int) -> float:
    """
    Converts a number in string format from base-N (2 to 16) to decimal (base-10).

    Args:
        value (str): The number in base-N (e.g., '1A.4', '101.01')
        base (int): The original base (between 2 and 16)

    Returns:
        float: The equivalent value in decimal
    """
    if not (2 <= base <= 16):
        raise ValueError("Base must be between 2 and 16.")

    value = value.strip().upper()
    is_negative = value.startswith("-")
    if is_negative:
        value = value[1:]

    int_part, frac_part = value.split(".") if "." in value else (value, "")
    digit_map = {ch: i for i, ch in enumerate(DIGITS[:base])}

    # Convert integer part
    result = 0
    for char in int_part:
        if char not in digit_map:
            raise ValueError(f"Invalid character '{char}' for base {base}")
        result = result * base + digit_map[char]

    # Convert fractional part
    for i, char in enumerate(frac_part, start=1):
        if char not in digit_map:
            raise ValueError(f"Invalid character '{char}' for base {base}")
        result += digit_map[char] / (base ** i)

    return -result if is_negative else result


def convert_from_decimal_to_base_n(number: float, base: int, decimal_places: int = 10) -> str:
    """
    Converts a decimal number (int or float) to a string representation in base-N (2 to 16).

    Args:
        number (float): The decimal number to convert
        base (int): The target base (between 2 and 16)
        decimal_places (int): Maximum number of digits after the decimal point

    Returns:
        str: The number represented in the target base (e.g., '1A.4', '111.01')
    """
    if not (2 <= base <= 16):
        raise ValueError("Base must be between 2 and 16.")
    if decimal_places < 0:
        raise ValueError("Decimal places must be non-negative.")

    is_negative = number < 0
    number = abs(number)

    integer_part = int(number)
    fractional_part = number - integer_part

    # Convert integer part
    int_result = "0" if integer_part == 0 else ""
    while integer_part > 0:
        int_result = DIGITS[integer_part % base] + int_result
        integer_part //= base

    # Convert fractional part
    frac_result = ""
    for _ in range(decimal_places):
        fractional_part *= base
        digit = int(fractional_part)
        frac_result += DIGITS[digit]
        fractional_part -= digit

    # Remove trailing zeros only if ALL are zero
    if frac_result and set(frac_result) == {"0"}:
        frac_result = ""

    result = int_result
    if frac_result:
        result += "." + frac_result
    elif number % 1 != 0:
        result += "." + "0" * decimal_places  # ensure fixed places if fraction requested

    return "-" + result if is_negative else result
