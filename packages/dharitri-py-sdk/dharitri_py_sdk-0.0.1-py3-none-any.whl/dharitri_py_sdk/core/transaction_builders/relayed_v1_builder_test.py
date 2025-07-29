import pytest

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.errors import ErrInvalidRelayerV1BuilderArguments
from dharitri_py_sdk.core.token_payment import TokenPayment
from dharitri_py_sdk.core.transaction import Transaction
from dharitri_py_sdk.core.transaction_builders.relayed_v1_builder import \
    RelayedTransactionV1Builder
from dharitri_py_sdk.core.transaction_computer import TransactionComputer
from dharitri_py_sdk.testutils.wallets import load_wallets


class NetworkConfig:
    def __init__(self) -> None:
        self.min_gas_limit = 50_000
        self.gas_per_data_byte = 1_500
        self.gas_price_modifier = 0.01
        self.chain_id = "T"


class TestRelayedV1Builder:
    wallets = load_wallets()
    alice = wallets["alice"]
    bob = wallets["bob"]
    frank = wallets["frank"]
    grace = wallets["grace"]
    carol = wallets["carol"]
    transaction_computer = TransactionComputer()

    def test_without_arguments(self):
        relayed_builder = RelayedTransactionV1Builder()

        with pytest.raises(ErrInvalidRelayerV1BuilderArguments):
            relayed_builder.build()

        inner_transaction = Transaction(
            chain_id="1",
            sender=self.alice.label,
            receiver="drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2",
            gas_limit=10000000,
            nonce=15,
            data=b"getContractConfig"
        )
        relayed_builder.set_inner_transaction(inner_transaction)

        with pytest.raises(ErrInvalidRelayerV1BuilderArguments):
            relayed_builder.build()

        network_config = NetworkConfig()
        relayed_builder.set_network_config(network_config)

        with pytest.raises(ErrInvalidRelayerV1BuilderArguments):
            relayed_builder.build()

    def test_compute_relayed_v1_tx(self):
        network_config = NetworkConfig()

        inner_tx = Transaction(
            chain_id=network_config.chain_id,
            sender=self.bob.label,
            receiver="drt1yvesqqqqqqqqqqqqqqqqqqqqqqqqyvesqqqqqqqqqqqqqqqzlllsd5j0s2",
            gas_limit=60000000,
            nonce=198,
            data=b"getContractConfig"
        )
        inner_tx.signature = self.bob.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))

        relayed_builder = RelayedTransactionV1Builder()
        relayed_builder.set_inner_transaction(inner_tx)
        relayed_builder.set_relayer_nonce(2627)
        relayed_builder.set_network_config(network_config)
        relayed_builder.set_relayer_address(Address.new_from_bech32(self.alice.label))

        relayed_tx = relayed_builder.build()
        relayed_tx.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(relayed_tx))

        assert relayed_tx.nonce == 2627
        assert relayed_tx.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22497a4d4141414141414141414141414141414141414141434d7a41414141414141414141414141432f2f383d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225a3256305132397564484a68593352446232356d6157633d222c227369676e6174757265223a22662f583030554a394e45755239345a7147316c7369514730755a4349724256513247566b66494b5972422f2b36586c4f6f43583550654d6d664953547957614c37376c6e5547336e397245627a7037743537396342673d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a327d"
        assert relayed_tx.signature.hex() == "724f97113a8f2b5851c1c5d918e06465cc0562f1d9c691ea94cb0a4f0b4633ff67e6769fed9c87d0d2a6518d924823b0310d721968bf37a42720cab382710d06"

    def test_compute_guarded_inner_tx(self):
        network_config = NetworkConfig()

        inner_tx = Transaction(
            chain_id=network_config.chain_id,
            sender=self.bob.label,
            receiver="drt1qqqqqqqqqqqqqpgq54tsxmej537z9leghvp69hfu4f8gg5eu396q6dlssu",
            gas_limit=60000000,
            nonce=198,
            data=b"getContractConfig",
            guardian=self.grace.label,
            version=2,
            options=2
        )
        inner_tx.signature = self.bob.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))
        inner_tx.guardian_signature = self.grace.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))

        relayed_builder = RelayedTransactionV1Builder()
        relayed_builder.set_inner_transaction(inner_tx)
        relayed_builder.set_relayer_nonce(2627)
        relayed_builder.set_network_config(network_config)
        relayed_builder.set_relayer_address(Address.new_from_bech32(self.alice.label))

        relayed_tx = relayed_builder.build()
        relayed_tx.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(relayed_tx))

        assert relayed_tx.nonce == 2627
        assert relayed_tx.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22414141414141414141414146414b565841323879704877692f79693741364c64504b704f68464d386958513d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225a3256305132397564484a68593352446232356d6157633d222c227369676e6174757265223a223534646e2b7a726d737832304e67793838756f462b72546f443179447030524b563966714462574a5947365a784a33544132516377554a49426168704a52394d322b487637694a2f446f726c533863684973777143513d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c226f7074696f6e73223a322c22677561726469616e223a2273673076774659474759786e4847666f50566365784c6e704163476c72715536756459476b3676427a2b513d222c22677561726469616e5369676e6174757265223a2250382f395a59483768614833314763337241396139774771326b6c5a6e2f76616978656f7954742f707336752f6769515757754a583650344a54735a58566f4e744c57595a744554376e2b30723761556155504443773d3d227d"
        assert relayed_tx.signature.hex() == "357c4d189dfe71398e80e4f04d10c823f94eacd96b9dc304d4a67ccff5832c6a71e54eec0181f881b862da0347ad99fee2773ce1b5776a35ac25247384a37707"

    def test_guarded_inner_tx_and_guarded_relayed_tx(self):
        network_config = NetworkConfig()

        inner_tx = Transaction(
            chain_id=network_config.chain_id,
            sender=self.bob.label,
            receiver="drt1qqqqqqqqqqqqqpgq54tsxmej537z9leghvp69hfu4f8gg5eu396q6dlssu",
            gas_limit=60000000,
            nonce=198,
            data=b"addNumber",
            guardian=self.grace.label,
            version=2,
            options=2
        )
        inner_tx.signature = self.bob.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))
        inner_tx.guardian_signature = self.grace.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))

        relayed_builder = RelayedTransactionV1Builder()
        relayed_builder.set_inner_transaction(inner_tx)
        relayed_builder.set_relayer_nonce(2627)
        relayed_builder.set_network_config(network_config)
        relayed_builder.set_relayer_address(Address.new_from_bech32(self.alice.label))
        relayed_builder.set_relayed_transaction_version(2)
        relayed_builder.set_relayed_transaction_options(2)
        relayed_builder.set_relayed_transaction_guardian(Address.new_from_bech32(self.frank.label))

        relayed_tx = relayed_builder.build()
        relayed_tx.signature = self.alice.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(relayed_tx))
        relayed_tx.guardian_signature = self.frank.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))

        assert relayed_tx.nonce == 2627
        assert relayed_tx.data.decode() == "relayedTx@7b226e6f6e6365223a3139382c2273656e646572223a2250643858504a3443774f5750736556533948505a6a61616b772f493866674e4d6b533770696f33647a68633d222c227265636569766572223a22414141414141414141414146414b565841323879704877692f79693741364c64504b704f68464d386958513d222c2276616c7565223a302c226761735072696365223a313030303030303030302c226761734c696d6974223a36303030303030302c2264617461223a225957526b546e5674596d5679222c227369676e6174757265223a227a7a506a436a62676f7a62615348354655796e53484362663534514c38545635726c32722b6a4c486b4b37422f2b674f4151454e764e636d4d784a705745694c62716c4e5a35634f6b305563637a66326251716d44513d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c226f7074696f6e73223a322c22677561726469616e223a2273673076774659474759786e4847666f50566365784c6e704163476c72715536756459476b3676427a2b513d222c22677561726469616e5369676e6174757265223a22436f79665045623959312b5867413943762f42704f6370455a516f3347676d4442575a52714c7a773732343132686470444e362b6a7669325777676d306148756c412b7970382f6b4575673566346d715179466344673d3d227d"
        assert relayed_tx.signature.hex() == "cba1922740567512e09bb0499d875bb9407c2736ce1fd42247d76eb5149050ca33dd1dc7ebfbbf13e90d818407ab6025699346d7b0369be3cf483c335883e702"

    def test_compute_relayedV1_with_usernames(self):
        network_config = NetworkConfig()

        inner_tx = Transaction(
            chain_id=network_config.chain_id,
            sender=self.carol.label,
            receiver=self.alice.label,
            gas_limit=50000,
            sender_username="carol",
            receiver_username="alice",
            nonce=208,
            value=TokenPayment.rewa_from_amount(1).amount_as_integer
        )
        inner_tx.signature = self.carol.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(inner_tx))

        builder = RelayedTransactionV1Builder()
        builder.set_inner_transaction(inner_tx)
        builder.set_relayer_nonce(715)
        builder.set_network_config(network_config)
        builder.set_relayer_address(Address.new_from_bech32(self.frank.label))

        relayed_tx = builder.build()
        relayed_tx.signature = self.frank.secret_key.sign(self.transaction_computer.compute_bytes_for_signing(relayed_tx))

        assert relayed_tx.nonce == 715
        assert relayed_tx.data.decode() == "relayedTx@7b226e6f6e6365223a3230382c2273656e646572223a2273462f6c4e634a2f527045666450693338675563565065532f4b434d65724938552b642b7a7330733253673d222c227265636569766572223a2278344a434155546f4b57393163796930436441574d372b4e4364697245653577307977675432574a7653513d222c2276616c7565223a313030303030303030303030303030303030302c226761735072696365223a313030303030303030302c226761734c696d6974223a35303030302c2264617461223a22222c227369676e6174757265223a2259594156326c65624a67487a686c4b6d72586a575450427a4e6154522f4e4e31565845714b457a5a78525a3030393738756a6539564b486e6b383153654a416931666a3979394d7a4d393263554b44463943395941673d3d222c22636861696e4944223a2256413d3d222c2276657273696f6e223a322c22736e64557365724e616d65223a22593246796232773d222c22726376557365724e616d65223a22595778705932553d227d"
        assert relayed_tx.signature.hex() == "86c344f26dc7e223b039044b8f950d6597f758715969170b506c069e3bc25254bf7bffd5bdf564d4547f8c153a9962358138727be39726c527226be309430f0a"
