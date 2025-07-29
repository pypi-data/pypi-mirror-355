import re
from types import SimpleNamespace

import pytest

from dharitri_py_sdk.abi.address_value import AddressValue
from dharitri_py_sdk.core.address import Address


def test_set_payload_and_get_payload():
    # Simple
    pubkey = bytes.fromhex("c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24")
    value = AddressValue()
    value.set_payload(pubkey)
    assert value.get_payload() == pubkey

    # Simple (from Address)
    address = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    value = AddressValue()
    value.set_payload(address)
    assert value.get_payload() == address.get_public_key()

    # From dict using a bech32 address
    address = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    value = AddressValue()
    value.set_payload(
        {
            "bech32": address.to_bech32()
        }
    )
    assert value.get_payload() == address.get_public_key()

    # From dict using a hex address
    address = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    value = AddressValue()
    value.set_payload(
        {
            "hex": address.to_hex()
        }
    )
    assert value.get_payload() == address.get_public_key()

    # With errors
    with pytest.raises(ValueError, match=re.escape("public key (address) has invalid length: 3")):
        AddressValue().set_payload(bytes([1, 2, 3]))

    # With errors
    with pytest.raises(TypeError, match="cannot convert 'types.SimpleNamespace' object to bytes"):
        AddressValue().set_payload(SimpleNamespace(a=1, b=2, c=3))

    # With errors
    with pytest.raises(ValueError, match="cannot extract pubkey from dictionary: missing 'bech32' or 'hex' keys"):
        AddressValue().set_payload({})
