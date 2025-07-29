
import pytest

from dharitri_py_sdk.core.address import (Address, AddressComputer,
                                         AddressFactory, is_valid_bech32)
from dharitri_py_sdk.core.errors import ErrBadAddress, ErrBadPubkeyLength


def test_address():
    address = Address.new_from_bech32("drt1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsxvluwu")
    assert "fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293" == address.to_hex()
    assert "drt1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsxvluwu" == address.to_bech32()

    address = Address.new_from_hex("fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293", "drt")
    assert "fd691bb5e85d102687d81079dffce842d4dc328276d2d4c60d8fd1c3433c3293" == address.to_hex()
    assert "drt1l453hd0gt5gzdp7czpuall8ggt2dcv5zwmfdf3sd3lguxseux2fsxvluwu" == address.to_bech32()

    with pytest.raises(ErrBadPubkeyLength):
        address = Address(bytes(), "drt")

    with pytest.raises(ErrBadAddress):
        address = Address.new_from_bech32("bad")


def test_address_with_custom_hrp():
    address = Address.new_from_hex("c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24", "test")
    assert address.hrp == "test"
    assert address.to_bech32() == "test1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jqcq0sx4"

    address = Address.new_from_bech32("test1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jqcq0sx4")
    assert address.hrp == "test"
    assert address.to_hex() == "c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24"


def test_address_factory():
    factory_foo = AddressFactory("foo")
    factory_drt = AddressFactory("drt")
    pubkey = bytes.fromhex("c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24")

    assert factory_foo.create_from_public_key(pubkey).to_bech32() == "foo1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jqsycxlr"
    assert factory_drt.create_from_public_key(pubkey).to_bech32() == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"


def test_is_valid_bech32():
    assert is_valid_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l", "drt")
    assert is_valid_bech32("foo1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jqsycxlr", "foo")
    assert not is_valid_bech32("foobar", "foo")
    assert not is_valid_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l", "foo")


def test_get_address_shard():
    address_computer = AddressComputer()
    address = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    assert address_computer.get_shard_of_address(address) == 0

    address = Address.new_from_bech32("drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2")
    assert address_computer.get_shard_of_address(address) == 1

    address = Address.new_from_bech32("drt1kp072dwz0arfz8m5lzmlypgu2nme9l9q33aty0znualvanfvmy5qd3yy8q")
    assert address_computer.get_shard_of_address(address) == 0


def test_compute_contract_address():
    deployer = Address.new_from_bech32("drt1j0hxzs7dcyxw08c4k2nv9tfcaxmqy8rj59meq505w92064x0h40q96qj7l")
    address_computer = AddressComputer()

    contract_address = address_computer.compute_contract_address(deployer, deployment_nonce=0)
    assert contract_address.to_hex() == "00000000000000000500bb652200ed1f994200ab6699462cab4b1af7b11ebd5e"
    assert contract_address.to_bech32() == "drt1qqqqqqqqqqqqqpgqhdjjyq8dr7v5yq9tv6v5vt9tfvd00vg7h40q8zfxpd"

    contract_address = address_computer.compute_contract_address(deployer, deployment_nonce=1)
    assert contract_address.to_hex() == "000000000000000005006e4f90488e27342f9a46e1809452c85ee7186566bd5e"
    assert contract_address.to_bech32() == "drt1qqqqqqqqqqqqqpgqde8eqjywyu6zlxjxuxqfg5kgtmn3setxh40qy0s6t6"
