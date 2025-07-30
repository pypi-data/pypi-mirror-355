import re

# Maximum allowable Aptos account address value (256 bits)
MAX_APTOS_ADDRESS = 2**256


def is_valid_address(address: str) -> bool:
    """
    Check if the address is a valid Aptos account address.

    Requirements:
    - Must be a 32-byte (64 hex characters) string.
    - Must be an entire 64-character hex string, padded with leading zeros as needed.
    - Optional '0x' or '0X' prefix is allowed.
    - Numeric value must be < 2**256.
    """
    # Ensure input is a string
    if not isinstance(address, str):
        return False

    # Remove optional prefix
    hex_part = address[2:] if address.startswith(("0x", "0X")) else address

    # Must be exactly 64 hex characters
    if len(hex_part) != 64:
        return False
    if not re.fullmatch(r"[0-9a-fA-F]{64}", hex_part):
        return False

    # Convert to integer and check range
    try:
        value = int(hex_part, 16)
    except ValueError:
        return False

    return 0 <= value < MAX_APTOS_ADDRESS
