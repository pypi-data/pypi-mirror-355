from typing import List

import pytest

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.errors import InvalidInnerTransactionError
from dharitri_py_sdk.core.transaction import Transaction
from dharitri_py_sdk.core.transaction_computer import TransactionComputer
from dharitri_py_sdk.core.transactions_factories.relayed_transactions_factory import \
    RelayedTransactionsFactory
from dharitri_py_sdk.core.transactions_factories.transactions_factory_config import \
    TransactionsFactoryConfig
from dharitri_py_sdk.testutils.wallets import load_wallets


class TestRelayedTransactionsFactory:
    config = TransactionsFactoryConfig("T")
    factory = RelayedTransactionsFactory(config)
    transaction_computer = TransactionComputer()
    wallets = load_wallets()

    def test_create_relayed_v1_with_invalid_inner_tx(self):
        alice = self.wallets["alice"]

        inner_transaction = Transaction(
            sender=alice.label,
            receiver="drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2",
            gas_limit=10000000,
            data="getContractConfig".encode(),
            chain_id=self.config.chain_id
        )

        with pytest.raises(InvalidInnerTransactionError, match="The inner transaction is not signed"):
            self.factory.create_relayed_v1_transaction(
                inner_transaction=inner_transaction,
                relayer_address=Address.from_bech32(self.wallets["bob"].label)
            )

        inner_transaction.gas_limit = 0
        inner_transaction.signature = b"invalidsignature"

        with pytest.raises(InvalidInnerTransactionError, match="The gas limit is not set for the inner transaction"):
            self.factory.create_relayed_v1_transaction(
                inner_transaction=inner_transaction,
                relayer_address=Address.from_bech32(self.wallets["bob"].label)
            )

    def test_create_relayed_v1_transaction(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver="drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2",
            gas_limit=60000000,
            chain_id=self.config.chain_id,
            data=b"getContractConfig",
            nonce=198
        )

        inner_tx_bytes = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(inner_tx_bytes)

        relayed_transaction = self.factory.create_relayed_v1_transaction(
            inner_transaction=inner_transaction,
            relayer_address=Address.from_bech32(alice.label)
        )
        relayed_transaction.nonce = 2627

        relayed_tx_bytes = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = alice.secret_key.sign(relayed_tx_bytes)

        assert relayed_transaction.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22497a4d4141414141414141414141414141414141414141434d7a41414141414141414141414141432f2f383d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225a3256305132397564484a68593352446232356d6157633d222c227369676e6174757265223a22662f583030554a394e45755239345a7147316c7369514730755a4349724256513247566b66494b5972422f2b36586c4f6f43583550654d6d664953547957614c37376c6e5547336e397245627a7037743537396342673d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a327d"
        assert relayed_transaction.signature.hex() == "724f97113a8f2b5851c1c5d918e06465cc0562f1d9c691ea94cb0a4f0b4633ff67e6769fed9c87d0d2a6518d924823b0310d721968bf37a42720cab382710d06"

    def test_create_relayed_v1_transaction_with_usernames(self):
        alice = self.wallets["alice"]
        carol = self.wallets["carol"]
        frank = self.wallets["frank"]

        inner_transaction = Transaction(
            sender=carol.label,
            receiver=alice.label,
            gas_limit=50000,
            chain_id=self.config.chain_id,
            nonce=208,
            sender_username="carol",
            receiver_username="alice",
            value=1000000000000000000
        )

        inner_tx_bytes = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = carol.secret_key.sign(inner_tx_bytes)

        relayed_transaction = self.factory.create_relayed_v1_transaction(
            inner_transaction=inner_transaction,
            relayer_address=Address.from_bech32(frank.label)
        )
        relayed_transaction.nonce = 715

        relayed_tx_bytes = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = frank.secret_key.sign(relayed_tx_bytes)

        assert relayed_transaction.data.decode() == "relayedTx@7b226e6f6e6365223a3230382c2273656e646572223a2273462f6c4e634a2f527045666450693338675563565065532f4b434d65724938552b642b7a7330733253673d222c227265636569766572223a2278344a434155546f4b57393163796930436441574d372b4e4364697245653577307977675432574a7653513d222c2276616c7565223a313030303030303030303030303030303030302c226761735072696365223a313030303030303030302c226761734c696d6974223a35303030302c2264617461223a22222c227369676e6174757265223a2259594156326c65624a67487a686c4b6d72586a575450427a4e6154522f4e4e31565845714b457a5a78525a3030393738756a6539564b486e6b383153654a416931666a3979394d7a4d393263554b44463943395941673d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c22736e64557365724e616d65223a22593246796232773d222c22726376557365724e616d65223a22595778705932553d227d"
        assert relayed_transaction.signature.hex() == "86c344f26dc7e223b039044b8f950d6597f758715969170b506c069e3bc25254bf7bffd5bdf564d4547f8c153a9962358138727be39726c527226be309430f0a"

    def test_compute_relayed_v1_with_guarded_inner_tx(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]
        grace = self.wallets["grace"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver="drt1qqqqqqqqqqqqqpgq54tsxmej537z9leghvp69hfu4f8gg5eu396q6dlssu",
            gas_limit=60000000,
            chain_id=self.config.chain_id,
            data=b"getContractConfig",
            nonce=198,
            version=2,
            options=2,
            guardian=grace.label
        )

        inner_tx_bytes = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(inner_tx_bytes)
        inner_transaction.guardian_signature = grace.secret_key.sign(inner_tx_bytes)

        relayed_transaction = self.factory.create_relayed_v1_transaction(
            inner_transaction=inner_transaction,
            relayer_address=Address.from_bech32(alice.label)
        )
        relayed_transaction.nonce = 2627

        relayed_tx_bytes = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = alice.secret_key.sign(relayed_tx_bytes)

        assert relayed_transaction.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22414141414141414141414146414b565841323879704877692f79693741364c64504b704f68464d386958513d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225a3256305132397564484a68593352446232356d6157633d222c227369676e6174757265223a223534646e2b7a726d737832304e67793838756f462b72546f443179447030524b563966714462574a5947365a784a33544132516377554a49426168704a52394d322b487637694a2f446f726c533863684973777143513d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c226f7074696f6e73223a322c22677561726469616e223a2273673076774659474759786e4847666f50566365784c6e704163476c72715536756459476b3676427a2b513d222c22677561726469616e5369676e6174757265223a2250382f395a59483768614833314763337241396139774771326b6c5a6e2f76616978656f7954742f707336752f6769515757754a583650344a54735a58566f4e744c57595a744554376e2b30723761556155504443773d3d227d"
        assert relayed_transaction.signature.hex() == "357c4d189dfe71398e80e4f04d10c823f94eacd96b9dc304d4a67ccff5832c6a71e54eec0181f881b862da0347ad99fee2773ce1b5776a35ac25247384a37707"

    def test_guarded_relayed_v1_with_guarded_inner_tx(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]
        grace = self.wallets["grace"]
        frank = self.wallets["frank"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver="drt1qqqqqqqqqqqqqpgq54tsxmej537z9leghvp69hfu4f8gg5eu396q6dlssu",
            gas_limit=60000000,
            chain_id=self.config.chain_id,
            data=b"addNumber",
            nonce=198,
            version=2,
            options=2,
            guardian=grace.label
        )

        inner_tx_bytes = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(inner_tx_bytes)
        inner_transaction.guardian_signature = grace.secret_key.sign(inner_tx_bytes)

        relayed_transaction = self.factory.create_relayed_v1_transaction(
            inner_transaction=inner_transaction,
            relayer_address=Address.from_bech32(alice.label)
        )
        relayed_transaction.options = 2
        relayed_transaction.nonce = 2627
        relayed_transaction.guardian = frank.label

        relayed_tx_bytes = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = alice.secret_key.sign(relayed_tx_bytes)
        relayed_transaction.guardian_signature = frank.secret_key.sign(relayed_tx_bytes)

        assert relayed_transaction.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22414141414141414141414146414b565841323879704877692f79693741364c64504b704f68464d386958513d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225957526b546e5674596d5679222c227369676e6174757265223a227a7a506a436a62676f7a62615348354655796e53484362663534514c38545635726c32722b6a4c486b4b37422f2b674f4151454e764e636d4d784a705745694c62716c4e5a35634f6b305563637a66326251716d44513d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c226f7074696f6e73223a322c22677561726469616e223a2273673076774659474759786e4847666f50566365784c6e704163476c72715536756459476b3676427a2b513d222c22677561726469616e5369676e6174757265223a22436f79665045623959312b5867413943762f42704f6370455a516f3347676d4442575a52714c7a773732343132686470444e362b6a7669325777676d306148756c412b7970382f6b4575673566346d715179466344673d3d227d"
        assert relayed_transaction.signature.hex() == "cba1922740567512e09bb0499d875bb9407c2736ce1fd42247d76eb5149050ca33dd1dc7ebfbbf13e90d818407ab6025699346d7b0369be3cf483c335883e702"

    def test_create_relayed_v2_with_invalid_inner_tx(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]
        carol = self.wallets["carol"]

        inner_transaction = Transaction(
            sender=alice.label,
            receiver=bob.label,
            gas_limit=50000,
            chain_id=self.config.chain_id
        )

        with pytest.raises(InvalidInnerTransactionError, match="The gas limit should not be set for the inner transaction"):
            self.factory.create_relayed_v2_transaction(
                inner_transaction=inner_transaction,
                inner_transaction_gas_limit=50000,
                relayer_address=Address.from_bech32(carol.label)
            )

        inner_transaction.gas_limit = 0
        with pytest.raises(InvalidInnerTransactionError, match="The inner transaction is not signed"):
            self.factory.create_relayed_v2_transaction(
                inner_transaction=inner_transaction,
                inner_transaction_gas_limit=50000,
                relayer_address=Address.from_bech32(carol.label)
            )

    def test_compute_relayed_v2_transaction(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver="drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2",
            gas_limit=0,
            chain_id=self.config.chain_id,
            data=b"getContractConfig",
            nonce=15,
            version=2,
            options=0
        )

        serialized_inner_transaction = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(serialized_inner_transaction)

        relayed_transaction = self.factory.create_relayed_v2_transaction(
            inner_transaction=inner_transaction,
            inner_transaction_gas_limit=60_000_000,
            relayer_address=Address.from_bech32(alice.label)
        )
        relayed_transaction.nonce = 37

        serialized_relayed_transaction = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = alice.secret_key.sign(serialized_relayed_transaction)

        assert relayed_transaction.version == 2
        assert relayed_transaction.options == 0
        assert relayed_transaction.gas_limit == 60414500
        assert relayed_transaction.data.decode() == "relayedTxV2@233300000000000000000000000000000002333000000000000000000002ffff@0f@676574436f6e7472616374436f6e666967@374aa9bd1f21f05483a7be10d1262d07e73f822f93d7918fea4f041296161b163900bd375c8d345afd97eac521251a5f279e4fc7c18146ae51477934ddd2550f"

    def test_compute_relayed_v3_transaction(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver=bob.label,
            gas_limit=50000,
            chain_id="T",
            nonce=0,
            version=2,
            relayer=alice.label
        )

        inner_transactions = [inner_transaction]
        serialized_inner_transaction = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(serialized_inner_transaction)

        relayed_transaction = self.factory.create_relayed_v3_transaction(
            relayer_address=Address.from_bech32(alice.label),
            inner_transactions=inner_transactions
        )
        serialized_relayed_transaction = self.transaction_computer.compute_bytes_for_signing(relayed_transaction)
        relayed_transaction.signature = alice.secret_key.sign(serialized_relayed_transaction)
        assert relayed_transaction.signature.hex() == "be248e19b2a315c6e18daab28005e9e8f7c2f13ca8e13e3028e58f6054606c0a5db9953568856880668858050036593e923df607e59cf6d9314b0d291d25560c"
        assert relayed_transaction.gas_limit == 100000

    def test_create_relayed_v3_with_invalid_inner_tx(self):
        alice = self.wallets["alice"]
        bob = self.wallets["bob"]

        inner_transaction = Transaction(
            sender=bob.label,
            receiver="drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2",
            gas_limit=2500,
            chain_id="local-testnet",
            nonce=0,
            version=2,
            relayer="drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
        )

        serialized_inner_transaction = self.transaction_computer.compute_bytes_for_signing(inner_transaction)
        inner_transaction.signature = bob.secret_key.sign(serialized_inner_transaction)

        inner_transactions = [inner_transaction]

        """
        In the inner tx, the relayer address is acutally bob's. The creation should fail
        """
        with pytest.raises(InvalidInnerTransactionError) as err:
            self.factory.create_relayed_v3_transaction(
                relayer_address=Address.from_bech32(alice.label),
                inner_transactions=inner_transactions
            )
        assert str(err.value) == "The inner transaction has an incorrect relayer address"

        inner_transaction.signature = b""
        with pytest.raises(InvalidInnerTransactionError) as err:
            self.factory.create_relayed_v3_transaction(
                relayer_address=Address.from_bech32(alice.label),
                inner_transactions=inner_transactions
            )
        assert str(err.value) == "The inner transaction is not signed"

        inner_transactions: List[Transaction] = []
        with pytest.raises(InvalidInnerTransactionError) as err:
            self.factory.create_relayed_v3_transaction(
                relayer_address=Address.from_bech32(alice.label),
                inner_transactions=inner_transactions
            )
        assert str(err.value) == "The are no inner transactions"
