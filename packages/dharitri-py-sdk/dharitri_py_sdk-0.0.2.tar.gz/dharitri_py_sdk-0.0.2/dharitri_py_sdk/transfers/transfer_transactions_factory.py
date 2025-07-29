from typing import Optional

from dharitri_py_sdk.builders.token_transfers_data_builder import (
    TokenTransfersDataBuilder,
)
from dharitri_py_sdk.builders.transaction_builder import TransactionBuilder
from dharitri_py_sdk.core import Address, TokenComputer, TokenTransfer, Transaction
from dharitri_py_sdk.core.constants import REWA_IDENTIFIER_FOR_MULTI_DCDTNFT_TRANSFER
from dharitri_py_sdk.core.errors import BadUsageError
from dharitri_py_sdk.core.transactions_factory_config import TransactionsFactoryConfig

ADDITIONAL_GAS_FOR_DCDT_TRANSFER = 100000
ADDITIONAL_GAS_FOR_DCDT_NFT_TRANSFER = 800000


class TransferTransactionsFactory:
    def __init__(self, config: TransactionsFactoryConfig) -> None:
        self.config = config
        self.token_computer = TokenComputer()
        self._data_args_builder = TokenTransfersDataBuilder(self.token_computer)

    def create_transaction_for_native_token_transfer(
        self,
        sender: Address,
        receiver: Address,
        native_amount: int,
        data: Optional[str] = None,
    ) -> Transaction:
        transaction_data = data if data else ""
        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=[transaction_data],
            gas_limit=0,
            add_data_movement_gas=True,
            amount=native_amount,
        ).build()

    def create_transaction_for_dcdt_token_transfer(
        self, sender: Address, receiver: Address, token_transfers: list[TokenTransfer]
    ) -> Transaction:
        if not token_transfers:
            raise BadUsageError("No token transfer has been provided")

        if len(token_transfers) == 1:
            data_parts, extra_gas_for_transfer, receiver = self._single_transfer(sender, receiver, token_transfers[0])
        else:
            data_parts, extra_gas_for_transfer, receiver = self._multi_transfer(sender, receiver, token_transfers)

        return TransactionBuilder(
            config=self.config,
            sender=sender,
            receiver=receiver,
            data_parts=data_parts,
            gas_limit=extra_gas_for_transfer,
            add_data_movement_gas=True,
        ).build()

    def _single_transfer(
        self, sender: Address, receiver: Address, transfer: TokenTransfer
    ) -> tuple[list[str], int, Address]:
        if self.token_computer.is_fungible(transfer.token):
            if transfer.token.identifier == REWA_IDENTIFIER_FOR_MULTI_DCDTNFT_TRANSFER:
                data_parts = self._data_args_builder.build_args_for_multi_dcdt_nft_transfer(receiver, [transfer])
                gas = self.config.gas_limit_multi_dcdt_nft_transfer + ADDITIONAL_GAS_FOR_DCDT_NFT_TRANSFER
                return data_parts, gas, sender
            else:
                data_parts = self._data_args_builder.build_args_for_dcdt_transfer(transfer)
                gas = self.config.gas_limit_dcdt_transfer + ADDITIONAL_GAS_FOR_DCDT_TRANSFER
                return data_parts, gas, receiver

        data_parts = self._data_args_builder.build_args_for_single_dcdt_nft_transfer(transfer, receiver)
        gas = self.config.gas_limit_dcdt_nft_transfer + ADDITIONAL_GAS_FOR_DCDT_NFT_TRANSFER
        return data_parts, gas, sender

    def _multi_transfer(
        self, sender: Address, receiver: Address, token_transfers: list[TokenTransfer]
    ) -> tuple[list[str], int, Address]:
        data_parts = self._data_args_builder.build_args_for_multi_dcdt_nft_transfer(receiver, token_transfers)
        gas = (
            self.config.gas_limit_multi_dcdt_nft_transfer * len(token_transfers) + ADDITIONAL_GAS_FOR_DCDT_NFT_TRANSFER
        )
        return data_parts, gas, sender

    def create_transaction_for_transfer(
        self,
        sender: Address,
        receiver: Address,
        native_amount: Optional[int] = None,
        token_transfers: Optional[list[TokenTransfer]] = None,
        data: Optional[bytes] = None,
    ) -> Transaction:
        if token_transfers and data:
            raise BadUsageError("Can't set data field when sending dcdt tokens")

        if (native_amount and not token_transfers) or data:
            native_amount = native_amount if native_amount else 0
            return self.create_transaction_for_native_token_transfer(
                sender=sender,
                receiver=receiver,
                native_amount=native_amount,
                data=data.decode() if data else None,
            )

        token_transfers = list(token_transfers) if token_transfers else []

        native_transfer = TokenTransfer.new_from_native_amount(native_amount) if native_amount else None
        token_transfers.append(native_transfer) if native_transfer else None

        return self.create_transaction_for_dcdt_token_transfer(
            sender=sender, receiver=receiver, token_transfers=token_transfers
        )
