import pytest

from mm_apt.account import is_valid_address


# Helper to generate a full 64-char hex string with a given repeat char
def full_hex(ch):
    return ch * 64


def test_valid_full_length_addresses():
    # All zeros
    assert is_valid_address("0x" + full_hex("0")) is True
    # Mixed zeros and ones
    assert is_valid_address("0x" + "0" * 63 + "1") is True
    # All Fs (max minus 1)
    assert is_valid_address("0x" + full_hex("f")) is True
    # Uppercase hex
    assert is_valid_address("0X" + full_hex("A")) is True
    # Without prefix
    assert is_valid_address(full_hex("1")) is True


def test_invalid_full_length_addresses():
    # Too short
    short_hex = "0x" + "1" * 63
    assert is_valid_address(short_hex) is False
    # Too long
    long_hex = "0x" + "f" * 65
    assert is_valid_address(long_hex) is False
    # Invalid character
    bad_char = "0x" + "g" + "0" * 63
    assert is_valid_address(bad_char) is False
    # Numeric type
    assert is_valid_address(123) is False


def test_address_out_of_range():
    # Exactly 2**256 is out of range -> 1 followed by 64 zeros in hex is too large (65 hex digits)
    out_of_range = "0x1" + "0" * 64
    # It's invalid by length then by range
    assert is_valid_address(out_of_range) is False
    # Highest valid: 2**256 - 1 -> 64 hex 'f'
    max_valid = "0x" + full_hex("f")
    assert is_valid_address(max_valid) is True


def test_missing_prefix_short_address():
    # Even valid numeric value but missing prefix and not full-length
    assert is_valid_address("1" * 1) is False
    assert is_valid_address("a" * 10) is False


if __name__ == "__main__":
    pytest.main()
