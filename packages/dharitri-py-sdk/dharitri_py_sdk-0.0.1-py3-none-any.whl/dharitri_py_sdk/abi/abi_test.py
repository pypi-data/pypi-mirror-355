from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

from dharitri_py_sdk.abi.abi import Abi
from dharitri_py_sdk.abi.abi_definition import ParameterDefinition
from dharitri_py_sdk.abi.address_value import AddressValue
from dharitri_py_sdk.abi.biguint_value import BigUIntValue
from dharitri_py_sdk.abi.bytes_value import BytesValue
from dharitri_py_sdk.abi.counted_variadic_values import CountedVariadicValues
from dharitri_py_sdk.abi.enum_value import EnumValue
from dharitri_py_sdk.abi.fields import Field
from dharitri_py_sdk.abi.list_value import ListValue
from dharitri_py_sdk.abi.option_value import OptionValue
from dharitri_py_sdk.abi.small_int_values import U32Value, U64Value
from dharitri_py_sdk.abi.string_value import StringValue
from dharitri_py_sdk.abi.struct_value import StructValue
from dharitri_py_sdk.abi.variadic_values import VariadicValues
from dharitri_py_sdk.core.address import Address

testdata = Path(__file__).parent.parent / "testutils" / "testdata"


def test_abi():
    abi = Abi.load(testdata / "adder.abi.json")

    assert abi.definition.constructor.name == "constructor"
    assert abi.definition.constructor.inputs == [ParameterDefinition("initial_value", "BigUint")]
    assert abi.definition.constructor.outputs == []

    assert abi.definition.upgrade_constructor.name == "upgrade_constructor"
    assert abi.definition.upgrade_constructor.inputs == [ParameterDefinition("initial_value", "BigUint")]
    assert abi.definition.upgrade_constructor.outputs == []

    assert abi.definition.events == []

    assert abi.definition.endpoints[0].name == "getSum"
    assert abi.definition.endpoints[0].inputs == []
    assert abi.definition.endpoints[0].outputs == [ParameterDefinition("", "BigUint")]

    assert abi.definition.endpoints[1].name == "add"
    assert abi.definition.endpoints[1].inputs == [ParameterDefinition("value", "BigUint")]
    assert abi.definition.endpoints[1].outputs == []

    assert abi.definition.types.enums == {}
    assert abi.definition.types.structs == {}
    assert abi.custom_types_prototypes_by_name == {}

    assert abi.constructor_prototype.input_parameters == [BigUIntValue()]
    assert abi.constructor_prototype.output_parameters == []
    assert abi.upgrade_constructor_prototype.input_parameters == [BigUIntValue()]
    assert abi.upgrade_constructor_prototype.output_parameters == []

    assert abi.endpoints_prototypes_by_name["getSum"].input_parameters == []
    assert abi.endpoints_prototypes_by_name["getSum"].output_parameters == [BigUIntValue()]
    assert abi.endpoints_prototypes_by_name["add"].input_parameters == [BigUIntValue()]
    assert abi.endpoints_prototypes_by_name["add"].output_parameters == []


def test_abi_events():
    abi = Abi.load(testdata / "artificial.abi.json")

    assert len(abi.definition.events) == 1
    assert abi.events_prototypes_by_name["firstEvent"].fields[0].value == BigUIntValue()


def test_load_abi_with_counted_variadic():
    abi = Abi.load(testdata / "counted-variadic.abi.json")

    bar_prototype = abi.endpoints_prototypes_by_name["bar"]

    assert isinstance(bar_prototype.input_parameters[0], CountedVariadicValues)
    assert bar_prototype.input_parameters[0].items == []
    assert bar_prototype.input_parameters[0].item_creator
    assert bar_prototype.input_parameters[0].item_creator() == U32Value()

    assert isinstance(bar_prototype.input_parameters[1], CountedVariadicValues)
    assert bar_prototype.input_parameters[1].items == []
    assert bar_prototype.input_parameters[1].item_creator
    assert bar_prototype.input_parameters[1].item_creator() == BytesValue()


def test_encode_endpoint_input_parameters_artificial_contract():
    abi = Abi.load(testdata / "artificial.abi.json")

    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="yellow",
        values=[[42, "hello", True]]
    )

    assert len(encoded_values) == 3
    assert encoded_values[0].hex() == "2a"
    assert encoded_values[1].hex() == "hello".encode().hex()
    assert encoded_values[2].hex() == "01"


def test_decode_endpoint_output_parameters_artificial_contract():
    abi = Abi.load(testdata / "artificial.abi.json")

    decoded_values = abi.decode_endpoint_output_parameters(
        endpoint_name="blue",
        encoded_values=[
            "UTK-2f80e9".encode(),
            bytes([0x00]),
            bytes.fromhex("0de0b6b3a7640000")
        ]
    )

    assert decoded_values == [["UTK-2f80e9", 0, 1000000000000000000]]


def test_encode_endpoint_input_parameters_multisig_propose_batch():
    abi = Abi.load(testdata / "multisig-full.abi.json")

    alice = Address.from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    expected_encoded_values = [
        bytes.fromhex("05|c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24|000000080de0b6b3a7640000|010000000000e4e1c0|000000076578616d706c65|00000002000000020342000000020743".replace("|", ""))
    ]

    # All values untyped, structure as dictionary.
    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="proposeBatch",
        values=[
            [
                {
                    "__discriminant__": 5,
                    "0": {
                        "to": alice,
                        "rewa_amount": 1000000000000000000,
                        "endpoint_name": "example",
                        "arguments": [
                            bytes([0x03, 0x42]),
                            bytes([0x07, 0x43])
                        ],
                        "opt_gas_limit": 15_000_000
                    }
                }
            ]
        ]
    )

    assert encoded_values == expected_encoded_values

    # All values untyped, structure as simple object.
    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="proposeBatch",
        values=[
            [
                {
                    "__discriminant__": 5,
                    "0": SimpleNamespace(
                        to=alice,
                        rewa_amount=1000000000000000000,
                        endpoint_name="example",
                        arguments=[
                            bytes([0x03, 0x42]),
                            bytes([0x07, 0x43])
                        ],
                        opt_gas_limit=15_000_000
                    )
                }
            ]
        ]
    )

    assert encoded_values == expected_encoded_values

    # All values untyped, structure as simple object (custom class)
    class CallActionData:
        def __init__(self, to: Address, rewa_amount: int, endpoint_name: str, arguments: List[bytes], opt_gas_limit: Optional[int] = None):
            self.to = to
            self.rewa_amount = rewa_amount
            self.endpoint_name = endpoint_name
            self.arguments = arguments
            self.opt_gas_limit = opt_gas_limit

    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="proposeBatch",
        values=[
            [
                {
                    "__discriminant__": 5,
                    "0": CallActionData(
                        to=alice,
                        rewa_amount=1000000000000000000,
                        endpoint_name="example",
                        arguments=[
                            bytes([0x03, 0x42]),
                            bytes([0x07, 0x43])
                        ],
                        opt_gas_limit=15_000_000
                    )
                }
            ]
        ]
    )

    assert encoded_values == expected_encoded_values

    # Some values typed, structure as dictionary.
    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="proposeBatch",
        values=[
            [
                {
                    "__discriminant__": 5,
                    "0": {
                        "to": AddressValue.from_address(alice),
                        "rewa_amount": 1000000000000000000,
                        "endpoint_name": StringValue("example"),
                        "arguments": [
                            bytes([0x03, 0x42]),
                            bytes([0x07, 0x43])
                        ],
                        "opt_gas_limit": U64Value(15_000_000)
                    }
                }
            ]
        ]
    )

    # All values typed.
    encoded_values = abi.encode_endpoint_input_parameters(
        endpoint_name="proposeBatch",
        values=[
            VariadicValues(
                [
                    EnumValue(
                        discriminant=5,
                        fields=[
                            Field("0", StructValue([
                                Field("to", AddressValue.from_address(alice)),
                                Field("rewa_amount", BigUIntValue(1000000000000000000)),
                                Field("opt_gas_limit", OptionValue(U64Value(15_000_000))),
                                Field("endpoint_name", BytesValue(b"example")),
                                Field("arguments", ListValue([
                                    BytesValue(bytes([0x03, 0x42])),
                                    BytesValue(bytes([0x07, 0x43])),
                                ])),
                            ])),
                        ],
                    )
                ]
            )
        ]
    )

    assert encoded_values == expected_encoded_values


def test_decode_endpoint_output_parameters_multisig_get_pending_action_full_info():
    abi = Abi.load(testdata / "multisig-full.abi.json")

    data_hex = "".join([
        "0000002A",
        "0000002A",
        "05|c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24|000000080de0b6b3a7640000|010000000000e4e1c0|000000076578616d706c65|00000002000000020342000000020743",
        "00000002|c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24|3ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce17",
    ]).replace("|", "")

    data = bytes.fromhex(data_hex)
    [[action_full_info]] = abi.decode_endpoint_output_parameters("getPendingActionFullInfo", [data])

    assert action_full_info.action_id == 42
    assert action_full_info.group_id == 42
    assert action_full_info.action_data.__discriminant__ == 5

    action_data_0 = getattr(action_full_info.action_data, "0")
    assert action_data_0.to == Address.from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l").get_public_key()
    assert action_data_0.rewa_amount == 1000000000000000000
    assert action_data_0.opt_gas_limit == 15000000
    assert action_data_0.endpoint_name == b"example"
    assert action_data_0.arguments == [bytes([0x03, 0x42]), bytes([0x07, 0x43])]

    assert action_full_info.signers == [
        Address.from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l").get_public_key(),
        Address.from_bech32("drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2").get_public_key(),
    ]
