from starknet_py.hash.address import get_checksum_address

from mm_strk.account import is_address


def test_valid_addresses():
    # Compact lower-case and mixed-case hex strings
    assert is_address("0x1") is True
    assert is_address("0x123abc") is True
    assert is_address("0xabCdEf") is True
    assert is_address("0x0701234567890123456789012345678901234567890123456789012345678901") is True

    # Already checksummed address
    raw = "0xdeadbeef"
    checksummed = get_checksum_address(raw)
    assert is_address(checksummed) is True


def test_invalid_addresses():
    # Missing prefix or empty
    assert is_address("123abc") is False
    assert is_address("0x") is False
    assert is_address("") is False

    # Non-hex characters
    assert is_address("0x12G45") is False

    # Wrong type
    assert is_address(None) is False

    # Too many leading zeroes (invalid compact form)
    # e.g., 0x0123 should canonicalise to 0x123
    assert is_address("0x0123") is False
