def to_signed(value: int, bit_width: int) -> int:
    """Convert an unsigned integer `value` to a signed integer by interpreting
    its internal bit pattern as a two's complement representation with the
    specified `bit_width`.

    Args:
        value (int): The unsigned integer to convert (e.g., from 0 to 255 for a
            bit width of 8).
        bit_width (int): The bit width used for the two's complement
            representation (to determine which bit is the sign bit).

    Returns:
        int: The signed integer represented by the input value (e.g., from -128
            to 127 for a bit width of 8).

    Raises:
        ValueError: If `value` is outside the valid range for the given
            `bit_width`.
    """
    if not (0 <= value < (1 << bit_width)):
        raise ValueError(
            f"Value {value} out of range for {bit_width}-bit unsigned integer.")
    msb = 1 << (bit_width - 1)
    return (value & ~msb) - (value & msb)


def to_unsigned(value: int, bit_width) -> int:
    """Convert a signed integer `value` to an unsigned integer by interpreting
    its bit pattern as an unsigned integer representation (i.e. sum of powers of
    two) with the specified `bit_width`.

    Args:
        value (int): The signed integer to convert (e.g., from -128 to 127 for a
            bit width of 8).
        bit_width (int): The bit width used for the unsigned integer
            representation. Leading ones of negative inputs will be considered
            up to the bit width.

    Returns:
        int: The unsigned integer representation (e.g., from 0 to 255 for a
            bit width of 8).

    Raises:
        ValueError: If the `value` is outside the valid signed range for the
            given `bit_width`.
    """
    if not (-(1 << (bit_width - 1)) <= value < (1 << (bit_width - 1))):
        raise ValueError(
            f"Value {value} out of range for {bit_width}-bit signed integer")
    return value % (1 << bit_width)
