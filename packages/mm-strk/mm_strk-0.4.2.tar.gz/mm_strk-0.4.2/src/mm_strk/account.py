import re

# Maximum allowable value for a StarkNet address (251 bits)
MAX_STARKNET_ADDRESS = 2**251


def is_address(address: str) -> bool:
    """
    Validates a StarkNet address.

    - Must be a string starting with '0x'.
    - Hex part 1-64 chars.
    - Integer value < 2**251.
    - Accepts either:
      • Full 64-hex-character padded form.
      • Minimal form without leading zeros (canonical).
    """
    # Type and prefix
    if not isinstance(address, str) or not address.startswith("0x"):
        return False

    hex_part = address[2:]
    # Length and hex
    if len(hex_part) < 1 or len(hex_part) > 64:
        return False
    if not re.fullmatch(r"[0-9a-fA-F]+", hex_part):
        return False

    # Convert to integer and range check
    try:
        value = int(hex_part, 16)
    except ValueError:
        return False
    if value >= MAX_STARKNET_ADDRESS:
        return False

    # Full padded 64-char form
    if len(hex_part) == 64:
        return True

    # Minimal form (no leading zeros)
    canonical = hex(value)[2:]
    return hex_part.lower() == canonical
