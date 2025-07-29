import base64

import pytest

from dharitri_py_sdk.converters.transactions_converter import \
    TransactionsConverter
from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.transactions_outcome_parsers.resources import (
    SmartContractCallOutcome, TransactionEvent, TransactionLogs,
    TransactionOutcome)
from dharitri_py_sdk.core.transactions_outcome_parsers.smart_contract_transactions_outcome_parser import \
    SmartContractTransactionsOutcomeParser
from dharitri_py_sdk.network_providers.contract_results import \
    ContractResultItem as ContractResultItemOnNetwork
from dharitri_py_sdk.network_providers.contract_results import \
    ContractResults as ContractResultOnNetwork
from dharitri_py_sdk.network_providers.proxy_network_provider import \
    ProxyNetworkProvider
from dharitri_py_sdk.network_providers.transaction_events import \
    TransactionEvent as TxEventOnNetwork
from dharitri_py_sdk.network_providers.transaction_events import \
    TransactionEventTopic as TxEventTopicOnNetwork
from dharitri_py_sdk.network_providers.transaction_logs import \
    TransactionLogs as TxLogsOnNetwork
from dharitri_py_sdk.network_providers.transactions import TransactionOnNetwork


class TestSmartContractTransactionsOutcomeParser:
    parser = SmartContractTransactionsOutcomeParser()

    def test_parse_minimalistic_deploy_outcome(self):
        contract = Address.new_from_bech32("drt1qqqqqqqqqqqqqpgqqacl85rd0gl2q8wggl8pwcyzcr4fflc5d8ss39zhmv")
        deployer = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        code_hash = b"abba"

        event = TransactionEvent(
            identifier="SCDeploy",
            topics=[contract.get_public_key(), deployer.get_public_key(), code_hash]
        )

        logs = TransactionLogs(events=[event])
        direct_sc_call_outcome = SmartContractCallOutcome(return_code="ok", return_message="ok")

        transaction_outcome = TransactionOutcome(
            direct_smart_contract_call_outcome=direct_sc_call_outcome,
            transaction_logs=logs
        )

        parsed = self.parser.parse_deploy(transaction_outcome)
        assert parsed.return_code == "ok"
        assert parsed.return_message == "ok"
        assert len(parsed.contracts) == 1
        assert parsed.contracts[0].address == contract.to_bech32()
        assert parsed.contracts[0].owner_address == deployer.to_bech32()
        assert parsed.contracts[0].code_hash == code_hash

    def test_parse_deploy_outcome(self):
        contract = Address.new_from_bech32("drt1qqqqqqqqqqqqqpgqqacl85rd0gl2q8wggl8pwcyzcr4fflc5d8ss39zhmv")
        deployer = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        code_hash = bytes.fromhex("abba")

        transaction_converter = TransactionsConverter()

        event = TxEventOnNetwork()
        event.identifier = "SCDeploy"
        event.topics = [
            TxEventTopicOnNetwork(base64.b64encode(contract.get_public_key()).decode()),
            TxEventTopicOnNetwork(base64.b64encode(deployer.get_public_key()).decode()),
            TxEventTopicOnNetwork(base64.b64encode(code_hash).decode())
        ]

        logs = TxLogsOnNetwork()
        logs.events = [event]

        item = ContractResultItemOnNetwork()
        item.nonce = 8
        item.data = "@6f6b"
        contract_result = ContractResultOnNetwork([item])

        tx_on_network = TransactionOnNetwork()
        tx_on_network.nonce = 7
        tx_on_network.logs = logs
        tx_on_network.contract_results = contract_result

        tx_outcome = transaction_converter.transaction_on_network_to_outcome(tx_on_network)

        parsed = self.parser.parse_deploy(tx_outcome)

        assert parsed.return_code == ""
        assert parsed.return_message == ""
        assert len(parsed.contracts) == 1
        assert parsed.contracts[0].address == contract.to_bech32()
        assert parsed.contracts[0].owner_address == deployer.to_bech32()
        assert parsed.contracts[0].code_hash == code_hash

    def test_parse_deploy_outcome_with_error(self):
        deployer = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        transaction_converter = TransactionsConverter()

        event = TxEventOnNetwork()
        event.identifier = "signalError"
        event.topics = [
            TxEventTopicOnNetwork(base64.b64encode(deployer.get_public_key()).decode()),
            TxEventTopicOnNetwork(base64.b64encode(b"wrong number of arguments").decode()),
        ]
        event.data = "@75736572206572726f72"

        logs = TxLogsOnNetwork()
        logs.events = [event]

        tx_on_network = TransactionOnNetwork()
        tx_on_network.nonce = 7
        tx_on_network.logs = logs

        tx_outcome = transaction_converter.transaction_on_network_to_outcome(tx_on_network)

        parsed = self.parser.parse_deploy(tx_outcome)

        assert parsed.return_code == ""
        assert parsed.return_message == ""
        assert len(parsed.contracts) == 0
        assert parsed.contracts == []

    @pytest.mark.networkInteraction
    def test_parse_successful_deploy(self):
        successful_tx_hash = "30bc4f262543e235b73ae6db7bcbf3a54513fe3c1ed7a86af688a8f0e7fe8655"
        proxy = ProxyNetworkProvider("https://devnet-gateway.dharitri.org")
        tx_converter = TransactionsConverter()

        tx_on_network = proxy.get_transaction(successful_tx_hash)
        tx_outcome = tx_converter.transaction_on_network_to_outcome(tx_on_network)

        parsed = self.parser.parse_deploy(tx_outcome)
        assert parsed.contracts[0].address == "drt1qqqqqqqqqqqqqpgq29deu3uhcvuk7jhxd5cxrvh23xulkcewd8sse4xy6x"
        assert parsed.contracts[0].owner_address == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"

    @pytest.mark.networkInteraction
    def test_parse_failed_deploy(self):
        faied_tx_hash = "832780459c6c9589035dbbe5b8d1d86ca9674f4aab8379cbca9a94978e604ffd"
        proxy = ProxyNetworkProvider("https://devnet-gateway.dharitri.org")
        tx_converter = TransactionsConverter()

        tx_on_network = proxy.get_transaction(faied_tx_hash)
        tx_outcome = tx_converter.transaction_on_network_to_outcome(tx_on_network)

        parsed = self.parser.parse_deploy(tx_outcome)
        assert len(parsed.contracts) == 0
        assert parsed.contracts == []
