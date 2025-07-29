import threading
import time
from typing import Any, Callable, Dict, List

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.interfaces import IAddress
from dharitri_py_sdk.core.transaction import Transaction
from dharitri_py_sdk.core.transaction_computer import TransactionComputer
from dharitri_py_sdk.network_providers.accounts import AccountOnNetwork
from dharitri_py_sdk.network_providers.contract_query_response import \
    ContractQueryResponse
from dharitri_py_sdk.network_providers.contract_results import (
    ContractResultItem, ContractResults)
from dharitri_py_sdk.network_providers.interface import IContractQuery
from dharitri_py_sdk.network_providers.transaction_status import \
    TransactionStatus
from dharitri_py_sdk.network_providers.transactions import TransactionOnNetwork
from dharitri_py_sdk.testutils.utils import create_account_rewa_balance


class MockNetworkProvider:
    alice = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    bob = Address.new_from_bech32("drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2")
    carol = Address.new_from_bech32("drt1kp072dwz0arfz8m5lzmlypgu2nme9l9q33aty0znualvanfvmy5qd3yy8q")

    def __init__(self) -> None:
        self.transactions: Dict[str, TransactionOnNetwork] = {}

        alice_account = AccountOnNetwork()
        alice_account.address = MockNetworkProvider.alice
        alice_account.nonce = 0
        alice_account.balance = create_account_rewa_balance(1000)

        bob_account = AccountOnNetwork()
        bob_account.address = MockNetworkProvider.bob
        bob_account.nonce = 5
        bob_account.balance = create_account_rewa_balance(500)

        carol_account = AccountOnNetwork()
        carol_account.address = MockNetworkProvider.carol
        carol_account.nonce = 42
        carol_account.balance = create_account_rewa_balance(300)

        self.accounts: Dict[str, AccountOnNetwork] = {
            MockNetworkProvider.alice.to_bech32(): alice_account,
            MockNetworkProvider.bob.to_bech32(): bob_account,
            MockNetworkProvider.carol.to_bech32(): carol_account
        }
        self.query_contract_responders: List[QueryContractResponder] = []
        self.get_transaction_responders: List[GetTransactionResponder] = []

    def mock_update_account(self, address: Address, mutate: Callable[[AccountOnNetwork], None]) -> None:
        account = self.accounts.get(address.to_bech32(), None)

        if account:
            mutate(account)

    def mock_update_transaction(self, hash: str, mutate: Callable[[TransactionOnNetwork], None]) -> None:
        transaction = self.transactions.get(hash, None)

        if transaction:
            mutate(transaction)

    def mock_put_transaction(self, hash: str, transaction: TransactionOnNetwork) -> None:
        transaction.is_completed = False
        self.transactions[hash] = transaction

    def mock_query_contract_on_function(self, function: str, response: ContractQueryResponse) -> None:
        def predicate(query: IContractQuery) -> bool:
            return query.get_function() == function

        self.query_contract_responders.append(QueryContractResponder(predicate, response))

    def mock_get_transaction_with_any_hash_as_completed_with_one_result(self, return_code_and_data: str) -> None:
        contract_result_item = ContractResultItem()
        contract_result_item.nonce = 1
        contract_result_item.data = return_code_and_data

        def predicate(hash: str) -> bool:
            return True

        response = TransactionOnNetwork()
        response.status = TransactionStatus("executed")
        response.contract_results = ContractResults([contract_result_item])
        response.is_completed = True

        self.get_transaction_responders.insert(0, GetTransactionResponder(predicate, response))

    def mock_transaction_timeline(self, transaction: Transaction, timeline_points: List[Any]) -> None:
        tx_computer = TransactionComputer()
        tx_hash = tx_computer.compute_transaction_hash(transaction).hex()
        self.mock_transaction_timeline_by_hash(tx_hash, timeline_points)

    def mock_transaction_timeline_by_hash(self, hash: str, timeline_points: List[Any]) -> None:
        def fn():
            for point in timeline_points:
                if isinstance(point, TransactionStatus):
                    def set_tx_status(transaction: TransactionOnNetwork):
                        transaction.status = point

                    self.mock_update_transaction(hash, set_tx_status)

                elif isinstance(point, TimelinePointMarkCompleted):
                    def mark_tx_as_completed(transaction: TransactionOnNetwork):
                        transaction.is_completed = True

                    self.mock_update_transaction(hash, mark_tx_as_completed)

                elif isinstance(point, TimelinePointWait):
                    time.sleep(point.milliseconds // 1000)

        thread = threading.Thread(target=fn)
        thread.start()

    def get_account(self, address: IAddress) -> AccountOnNetwork:
        account = self.accounts.get(address.to_bech32(), None)

        if account:
            return account

        raise Exception("Account not found")

    def get_transaction(self, tx_hash: str) -> TransactionOnNetwork:
        for responder in self.get_transaction_responders:
            if responder.matches(tx_hash):
                return responder.response

        transaction = self.transactions.get(tx_hash, None)
        if transaction:
            return transaction

        raise Exception("Transaction not found")

    def get_transaction_status(self, tx_hash: str) -> TransactionStatus:
        transaction = self.get_transaction(tx_hash)
        return transaction.status

    def query_contract(self, query: IContractQuery) -> ContractQueryResponse:
        for responder in self.query_contract_responders:
            if responder.matches(query):
                return responder.response

        raise Exception("No query response to return")


class QueryContractResponder:
    def __init__(self, matches: Callable[[IContractQuery], bool], response: ContractQueryResponse) -> None:
        self.matches = matches
        self.response = response


class GetTransactionResponder:
    def __init__(self, matches: Callable[[str], bool], response: TransactionOnNetwork) -> None:
        self.matches = matches
        self.response = response


class TimelinePointWait:
    def __init__(self, time_in_milliseconds: int) -> None:
        self.milliseconds = time_in_milliseconds


class TimelinePointMarkCompleted:
    pass
