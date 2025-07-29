from pathlib import Path

from dharitri_py_sdk.core.address import Address
from dharitri_py_sdk.core.constants import SDK_PY_SIGNER, UNKNOWN_SIGNER
from dharitri_py_sdk.core.message import Message, MessageComputer
from dharitri_py_sdk.wallet.user_signer import UserSigner
from dharitri_py_sdk.wallet.user_verifer import UserVerifier

parent = Path(__file__).parent.parent
message_computer = MessageComputer()
alice = Address.new_from_bech32("drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l")


def test_message_v1_serialize_for_signing():
    message = Message(
        data="test message".encode()
    )
    serialized = message_computer.compute_bytes_for_signing(message)
    assert serialized.hex() == "0f6fce3fa6130fc58a25eaff6e157ea1bcb02fbf9773dca514dfaf3cd1e0bdfe"


def test_sign_packed_message_and_verify_unpacked_message():
    message = Message(
        data="test".encode(),
        address=alice
    )

    signer = UserSigner.from_pem_file(parent / "testutils" / "testwallets" / "alice.pem")
    message.signature = signer.sign(message_computer.compute_bytes_for_signing(message))
    assert message.signature.hex() == "4b9b9293d7aa63b012641485865027adef8b4d4351d27f59ae62979acd49b328876c2fce97a2bed20f2ac12180155494ce1a1dc6103ec78a1ed32c6132734004"

    packed_message = message_computer.pack_message(message)
    assert packed_message == {
        "address": "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l",
        "message": "74657374",
        "signature": "4b9b9293d7aa63b012641485865027adef8b4d4351d27f59ae62979acd49b328876c2fce97a2bed20f2ac12180155494ce1a1dc6103ec78a1ed32c6132734004",
        "version": 1,
        "signer": SDK_PY_SIGNER
    }

    unpacked_message = message_computer.unpack_message(packed_message)
    assert unpacked_message.address
    assert unpacked_message.address.to_bech32() == alice.to_bech32()
    assert unpacked_message.data == message.data
    assert unpacked_message.signature == message.signature
    assert unpacked_message.version == message.version

    verifier = UserVerifier.from_address(unpacked_message.address)
    assert verifier.verify(message_computer.compute_bytes_for_verifying(unpacked_message), unpacked_message.signature)


def test_unpack_legacy_message():
    legacy_message = {
        "address": "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l",
        "message": "0x7468697320697320612074657374206d657373616765",
        "signature": "0xb16847437049986f936dd4a0917c869730cbf29e40a0c0821ca70db33f44758c3d41bcbea446dee70dea13d50942343bb78e74979dc434bbb2b901e0f4fd1809",
        "version": 1,
        "signer": "DrtJS"
    }
    message = message_computer.unpack_message(legacy_message)

    assert message.address
    assert message.address.to_bech32() == alice.to_bech32()
    assert message.data.decode() == "this is a test message"
    assert message.signature.hex() == "b16847437049986f936dd4a0917c869730cbf29e40a0c0821ca70db33f44758c3d41bcbea446dee70dea13d50942343bb78e74979dc434bbb2b901e0f4fd1809"
    assert message.version == 1
    assert message.signer == "DrtJS"


def test_unpack_message():
    packed_message = {
        "address": "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l",
        "message": "0x7468697320697320612074657374206d657373616765",
        "signature": "0xb16847437049986f936dd4a0917c869730cbf29e40a0c0821ca70db33f44758c3d41bcbea446dee70dea13d50942343bb78e74979dc434bbb2b901e0f4fd1809"
    }

    message = message_computer.unpack_message(packed_message)
    assert message.address
    assert message.address.to_bech32() == alice.to_bech32()
    assert message.data.decode() == "this is a test message"
    assert message.signature.hex() == "b16847437049986f936dd4a0917c869730cbf29e40a0c0821ca70db33f44758c3d41bcbea446dee70dea13d50942343bb78e74979dc434bbb2b901e0f4fd1809"
    assert message.version == 1
    assert message.signer == UNKNOWN_SIGNER
