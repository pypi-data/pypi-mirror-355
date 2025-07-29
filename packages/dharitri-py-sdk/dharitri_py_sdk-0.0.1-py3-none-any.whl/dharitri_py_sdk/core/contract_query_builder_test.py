from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.contract_query_builder import ContractQueryBuilder


def test_contract_query_builder():
    contract = Address.new_from_bech32("drt1qqqqqqqqqqqqqpgquzmh78klkqwt0p4rjys0qtp3la07gz4d396qwgcss9")
    caller = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")

    builder = ContractQueryBuilder(
        contract=contract,
        function="getFoobar",
        call_arguments=[42, "test", -836623209073744937290891644],
        caller=caller,
        value=1
    )

    query = builder.build()

    assert query.contract == contract
    assert query.function == "getFoobar"
    assert query.encoded_arguments == ["2a", "74657374", "fd4bf624f561bc2894c6fe84"]
    assert query.caller == caller
    assert query.value == 1
