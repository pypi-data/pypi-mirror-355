from dharitri_py_sdk.core.proto.transaction_serializer import ProtoSerializer
from dharitri_py_sdk.core.transaction import Transaction
from dharitri_py_sdk.core.transaction_computer import TransactionComputer
from dharitri_py_sdk.testutils.wallets import load_wallets


class TestProtoSerializer:
    wallets = load_wallets()
    alice = wallets["alice"]
    bob = wallets["bob"]
    carol = wallets["carol"]
    proto_serializer = ProtoSerializer()
    transaction_computer = TransactionComputer()

    def test_serialize_tx_no_data_no_value(self):
        transaction = Transaction(
            sender=self.alice.label,
            receiver=self.bob.label,
            gas_limit=50000,
            chain_id="local-testnet",
            nonce=89,
            value=0,
        )
        transaction.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(transaction))

        serialized_transaction = self.proto_serializer.serialize_transaction(transaction)
        assert serialized_transaction.hex() == "0859120200001a203ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce172a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24388094ebdc0340d08603520d6c6f63616c2d746573746e657458026240608e79523dc2d9e226ba820b41f541033b419509e5d2a7c0ebb4dabe2e7f353b854cc2861516969e8cc4396b25064eb300ea2beee2a036dea38847c8aa273509"

    def test_serialize_tx_with_data_no_value(self):
        transaction = Transaction(
            sender=self.alice.label,
            receiver=self.bob.label,
            gas_limit=80000,
            chain_id="local-testnet",
            data=b"hello",
            nonce=90
        )
        transaction.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(transaction))

        serialized_transaction = self.proto_serializer.serialize_transaction(transaction)
        assert serialized_transaction.hex() == "085a120200001a203ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce172a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24388094ebdc034080f1044a0568656c6c6f520d6c6f63616c2d746573746e65745802624058bf879780ef82367595bac476a2e17c9d0c6df2ecf36e02b6ea24f068ce3e8a5e9bda8e54d8a8d996f2ff59b2b26771708b59cbc779b16fba5592efecd2120f"

    def test_serialize_tx_with_data_and_value(self):
        transaction = Transaction(
            sender=self.alice.label,
            receiver=self.bob.label,
            gas_limit=100000,
            chain_id="local-testnet",
            nonce=92,
            data=b"for the spaceship",
            value=123456789000000000000000000000
        )
        transaction.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(transaction))

        serialized_transaction = self.proto_serializer.serialize_transaction(transaction)
        assert serialized_transaction.hex() == "085c120e00018ee90ff6181f3761632000001a203ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce172a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24388094ebdc0340a08d064a11666f722074686520737061636573686970520d6c6f63616c2d746573746e657458026240113097fc14df2d2357847e6b6a88d02478833d436f79feb7f85700482bba5f373175f6c1429d1437eafe36f5a4a07da776caa944713ab925579b0deb69cce609"

    def test_serialize_tx_with_nonce_zero(self):
        transaction = Transaction(
            sender=self.alice.label,
            receiver=self.bob.label,
            chain_id="local-testnet",
            gas_limit=80000,
            nonce=0,
            value=0,
            data=b"hello",
            version=1
        )
        transaction.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(transaction))

        serialized_transaction = self.proto_serializer.serialize_transaction(transaction)
        assert serialized_transaction.hex() == "120200001a203ddf173c9e02c0e58fb1e552f473d98da6a4c3f23c7e034c912ee98a8dddce172a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd24388094ebdc034080f1044a0568656c6c6f520d6c6f63616c2d746573746e657458016240765d7a4449cab04b2359631018edbf598d9c5f0c492e5bd3a75f5330b5b152a9c5d81a14f3d1f36cb34a560fc37819191248654310bdeee8fa4eb9286c493c02"

    def test_serialized_tx_with_usernames(self):
        transaction = Transaction(
            sender=self.carol.label,
            receiver=self.alice.label,
            gas_limit=50000,
            chain_id="T",
            nonce=204,
            value=1000000000000000000,
            sender_username="carol",
            receiver_username="alice"
        )
        transaction.signature = self.carol.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(transaction))

        serialized_transaction = self.proto_serializer.serialize_transaction(transaction)
        assert serialized_transaction.hex() == "08cc011209000de0b6b3a76400001a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd242205616c6963652a20b05fe535c27f46911f74f8b7f2051c54f792fca08c7ab23c53e77ececd2cd92832056361726f6c388094ebdc0340d0860352015458026240d335ef8f4f56ba2c6647e0e7835d5aec751449f0b3fd91125cce42de9440fdb7ab7be51b754b42cad97a0d8c1c1263cb5dab97c63b315f03b82f08618abc2000"

    def test_serialized_tx_with_inner_txs(self):
        inner_transaction = Transaction(
            sender=self.carol.label,
            receiver=self.alice.label,
            gas_limit=50000,
            chain_id="T",
            nonce=204,
            value=1000000000000000000,
            sender_username="carol",
            receiver_username="alice"
        )
        inner_transaction.signature = self.carol.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_transaction))

        relayed_transaction = Transaction(
            sender=self.carol.label,
            receiver=self.alice.label,
            gas_limit=50000,
            chain_id="T",
            nonce=204,
            value=1000000000000000000,
            sender_username="carol",
            receiver_username="alice",
            relayer=self.carol.label,
            inner_transactions=[inner_transaction]
        )

        relayed_transaction.signature = self.carol.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(
            relayed_transaction))
        serialized_transaction = self.proto_serializer.serialize_transaction(relayed_transaction)
        assert serialized_transaction.hex() == "08cc011209000de0b6b3a76400001a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd242205616c6963652a20b05fe535c27f46911f74f8b7f2051c54f792fca08c7ab23c53e77ececd2cd92832056361726f6c388094ebdc0340d0860352015458026240bb0cd9fc1b990a855d02d9e8dbff646e213729ed71d34358c46a8796389e30700f67f3d2758ced749a87717d12fe07f3889c0ddaf74d2da1c16f7fd7afe5b70d820120b05fe535c27f46911f74f8b7f2051c54f792fca08c7ab23c53e77ececd2cd9288a01b10108cc011209000de0b6b3a76400001a20c782420144e8296f757328b409d01633bf8d09d8ab11ee70d32c204f6589bd242205616c6963652a20b05fe535c27f46911f74f8b7f2051c54f792fca08c7ab23c53e77ececd2cd92832056361726f6c388094ebdc0340d0860352015458026240d335ef8f4f56ba2c6647e0e7835d5aec751449f0b3fd91125cce42de9440fdb7ab7be51b754b42cad97a0d8c1c1263cb5dab97c63b315f03b82f08618abc2000"
