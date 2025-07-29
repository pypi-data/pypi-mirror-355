from typing import Dict

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.transactions_factories.account_transactions_factory import \
    AccountTransactionsFactory
from dharitri_py_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig


class TestAccountTransactionsFactory:
    config = TransactionsFactoryConfig("D")
    factory = AccountTransactionsFactory(config)

    def test_save_key_value(self):
        sender = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        pairs: Dict[bytes, bytes] = {}
        key = "key0".encode()
        value = "value0".encode()
        pairs[key] = value

        tx = self.factory.create_transaction_for_saving_key_value(
            sender=sender,
            key_value_pairs=pairs
        )

        assert tx.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.data.decode() == "SaveKeyValue@6b657930@76616c756530"
        assert tx.gas_limit == 271000

    def test_set_guardian(self):
        sender = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        guardian = Address.new_from_bech32("drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2")
        service_id = "DharitrITCSService"

        tx = self.factory.create_transaction_for_setting_guardian(
            sender=sender,
            guardian_address=guardian,
            service_id=service_id
        )

        assert tx.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.data.decode() == "SetGuardian@3ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce17@446861726974724954435353657276696365"
        assert tx.gas_limit == 475500

    def test_guard_account(self):
        sender = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        tx = self.factory.create_transaction_for_guarding_account(sender)

        assert tx.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.data.decode() == "GuardAccount"
        assert tx.gas_limit == 318000

    def test_unguard_account(self):
        sender = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")
        tx = self.factory.create_transaction_for_unguarding_account(sender)

        assert tx.sender == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.receiver == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
        assert tx.data.decode() == "UnGuardAccount"
        assert tx.gas_limit == 321000
