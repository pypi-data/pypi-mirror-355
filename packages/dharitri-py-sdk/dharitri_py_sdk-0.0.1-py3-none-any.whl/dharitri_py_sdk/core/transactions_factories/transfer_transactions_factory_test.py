import pytest

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.errors import BadUsageError
from dharitri_py_sdk.core.tokens import Token, TokenTransfer
from dharitri_py_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig
from dharitri_py_sdk.core.transactions_factories.transfer_transactions_factory import \
    TransferTransactionsFactory


class TestTransferTransactionsFactory:
    transfer_factory = TransferTransactionsFactory(TransactionsFactoryConfig("D"))
    alice = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
    bob = Address.new_from_bech32("drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2")

    def test_create_transaction_for_native_token_transfer_no_data(self):
        transaction = self.transfer_factory.create_transaction_for_native_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 50_000
        assert transaction.data == b""

    def test_create_transaction_for_native_token_transfer_with_data(self):
        transaction = self.transfer_factory.create_transaction_for_native_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
            data="test data"
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 63_500
        assert transaction.data == b"test data"

    def test_create_transaction_for_dcdt_transfer(self):
        foo_token = Token("FOO-123456")
        token_transfer = TokenTransfer(foo_token, 1000000)

        transaction = self.transfer_factory.create_transaction_for_dcdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[token_transfer]
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "DCDTTransfer@464f4f2d313233343536@0f4240"
        assert transaction.gas_limit == 410_000

    def test_create_transaction_for_nft_transfer(self):
        nft = Token("NFT-123456", 10)
        token_transfer = TokenTransfer(nft, 1)

        transaction = self.transfer_factory.create_transaction_for_dcdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[token_transfer]
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "DCDTNFTTransfer@4e46542d313233343536@0a@01@3ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce17"
        assert transaction.gas_limit == 1_210_500

    def test_create_transaction_for_multiple_nft_transfers(self):
        first_nft = Token("NFT-123456", 10)
        first_transfer = TokenTransfer(first_nft, 1)

        second_nft = Token("TEST-987654", 1)
        second_transfer = TokenTransfer(second_nft, 1)

        transaction = self.transfer_factory.create_transaction_for_dcdt_token_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "MultiDCDTNFTTransfer@3ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce17@02@4e46542d313233343536@0a@01@544553542d393837363534@01@01"
        assert transaction.gas_limit == 1_466_000

        second_transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            token_transfers=[first_transfer, second_transfer]
        )
        assert second_transaction == transaction

    def test_create_transaction_for_token_transfer_with_errors(self):
        with pytest.raises(BadUsageError, match="Can't set data field when sending dcdt tokens"):
            nft = Token("NFT-123456", 10)
            transfer = TokenTransfer(nft, 1)

            self.transfer_factory.create_transaction_for_transfer(
                sender=self.alice,
                receiver=self.bob,
                token_transfers=[transfer],
                data="hello".encode()
            )

    def test_create_transaction_for_native_transfer(self):
        transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 50_000

    def test_create_transaction_for_native_transfer_and_set_data_field(self):
        transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
            data="hello".encode()
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 1000000000000000000
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 57_500

    def test_create_transaction_for_notarizing(self):
        transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            data="hello".encode()
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.gas_limit == 57_500

    def test_create_transaction_for_token_transfer(self):
        first_nft = Token("NFT-123456", 10)
        first_transfer = TokenTransfer(first_nft, 1)

        second_nft = Token("TEST-987654", 1)
        second_transfer = TokenTransfer(second_nft, 1)

        transaction = self.transfer_factory.create_transaction_for_transfer(
            sender=self.alice,
            receiver=self.bob,
            native_amount=1000000000000000000,
            token_transfers=[first_transfer, second_transfer]
        )

        assert transaction.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert transaction.value == 0
        assert transaction.chain_id == "D"
        assert transaction.data.decode() == "MultiDCDTNFTTransfer@3ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce17@03@4e46542d313233343536@0a@01@544553542d393837363534@01@01@524557412d303030303030@@0de0b6b3a7640000"
        assert transaction.gas_limit == 1_727_500
