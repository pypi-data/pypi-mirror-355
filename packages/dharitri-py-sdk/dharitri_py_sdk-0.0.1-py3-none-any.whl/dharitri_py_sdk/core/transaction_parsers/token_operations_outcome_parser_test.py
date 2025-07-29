from dharitri_py_sdk.core import Address
from dharitri_py_sdk.core.codec import encode_unsigned_number
from dharitri_py_sdk.core.transaction_parsers.token_operations_outcome_parser import \
    TokenOperationsOutcomeParser
from dharitri_py_sdk.core.transaction_parsers.transaction_on_network_wrapper import (
    ContractResultsWrapper, TransactionEventTopicWrapper,
    TransactionEventWrapper, TransactionLogsWrapper,
    TransactionOnNetworkWrapper)
from dharitri_py_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig

frank = Address.new_from_bech32("drt10xpcr2cqud9vm6q4axfv64ek63k7xywfcy8zyjp7pvx3kr4cnqlqv3scy7")
grace = Address.new_from_bech32("drt1kgxjlszkqcvccecuvl5r64c7cju7jqwp5kh22w4e6crf827peljqcvleft")
parser = TokenOperationsOutcomeParser(TransactionsFactoryConfig("D"))


def test_parse_issue_fungible():
    transaction = TransactionOnNetworkWrapper(
        ContractResultsWrapper([]),
        TransactionLogsWrapper([
            TransactionEventWrapper(
                address=frank,
                identifier="issue",
                topics=[TransactionEventTopicWrapper("FOOBAR".encode())],
                data=""
            )
        ])
    )

    outcome = parser.parse_issue_fungible(transaction)
    assert outcome.token_identifier == "FOOBAR"


def test_parse_set_special_role():
    transaction = TransactionOnNetworkWrapper(
        ContractResultsWrapper([]),
        TransactionLogsWrapper([
            TransactionEventWrapper(
                address=grace,
                identifier="DCDTSetRole",
                topics=[
                    TransactionEventTopicWrapper("FOOBAR".encode()),
                    TransactionEventTopicWrapper("".encode()),
                    TransactionEventTopicWrapper("".encode()),
                    TransactionEventTopicWrapper("DCDTRoleLocalMint".encode()),
                    TransactionEventTopicWrapper("DCDTRoleLocalBurn".encode())
                ],
                data=""
            )
        ])
    )

    outcome = parser.parse_set_special_role(transaction)
    assert outcome.token_identifier == "FOOBAR"
    assert outcome.roles == ["DCDTRoleLocalMint", "DCDTRoleLocalBurn"]
    assert outcome.user_address == grace.to_bech32()


def test_parse_local_mint():
    transaction = TransactionOnNetworkWrapper(
        ContractResultsWrapper([]),
        TransactionLogsWrapper([
            TransactionEventWrapper(
                address=grace,
                identifier="DCDTLocalMint",
                topics=[
                    TransactionEventTopicWrapper("FOOBAR".encode()),
                    TransactionEventTopicWrapper("".encode()),
                    TransactionEventTopicWrapper(encode_unsigned_number(200))
                ],
                data=""
            )
        ])
    )

    outcome = parser.parse_local_mint(transaction)
    assert outcome.token_identifier == "FOOBAR"
    assert outcome.nonce == 0
    assert outcome.minted_supply == 200
    assert outcome.user_address == grace.to_bech32()


def test_parse_nft_create():
    transaction = TransactionOnNetworkWrapper(
        ContractResultsWrapper([]),
        TransactionLogsWrapper([
            TransactionEventWrapper(
                address=grace,
                identifier="DCDTNFTCreate",
                topics=[
                    TransactionEventTopicWrapper("FOOBAR".encode()),
                    TransactionEventTopicWrapper(encode_unsigned_number(42)),
                    TransactionEventTopicWrapper(encode_unsigned_number(1))
                ],
                data=""
            )
        ])
    )

    outcome = parser.parse_nft_create(transaction)
    assert outcome.token_identifier == "FOOBAR"
    assert outcome.nonce == 42
    assert outcome.initial_quantity == 1
