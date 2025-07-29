
from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.transaction_builders.default_configuration import \
    DefaultTransactionBuildersConfiguration
from dharitri_py_sdk.core.transaction_builders.dcdt_builders import \
    DCDTIssueBuilder

dummyConfig = DefaultTransactionBuildersConfiguration(chain_id="D")


def test_dcdt_issue_builder():
    issuer = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")

    builder = DCDTIssueBuilder(
        config=dummyConfig,
        issuer=issuer,
        token_name="FOO",
        token_ticker="FOO",
        initial_supply=1000000000000,
        num_decimals=8,
        can_freeze=True,
        can_mint=True,
        can_upgrade=True
    )

    payload = builder.build_payload()
    tx = builder.build()

    assert payload.data == b"issue@464f4f@464f4f@e8d4a51000@08@63616e467265657a65@74727565@63616e4d696e74@74727565@63616e55706772616465@74727565@63616e4164645370656369616c526f6c6573@66616c7365"
    assert tx.chain_id == "D"
    assert tx.sender == issuer.to_bech32()
    assert tx.receiver == "drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2"
    assert tx.gas_limit == 50000 + payload.length() * 1500 + 60000000
    assert tx.data.decode() == str(payload)
