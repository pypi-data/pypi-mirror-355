
from pathlib import Path

from dharitri_py_sdk.wallet.constants import USER_SEED_LENGTH
from dharitri_py_sdk.wallet.pem_entry import PemEntry

testwallets = Path(__file__).parent.parent / "testutils" / "testwallets"


def test_from_text_all():
    text = (testwallets / "alice.pem").read_text()
    entries = PemEntry.from_text_all(text)
    entry = entries[0]
    assert len(entries) == 1
    assert entry.label == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
    assert entry.message[0:USER_SEED_LENGTH].hex() == "7b4686f3c925f9f6571de5fa24fb6a7ac0a2e5439a48bad8ed90b6690aad6017"

    text = (testwallets / "multipleUserKeys.pem").read_text()
    entries = PemEntry.from_text_all(text)
    entry = entries[0]
    assert len(entries) == 3
    assert entry.label == "drt1c7pyyq2yaq5k7atn9z6qn5qkxwlc6zwc4vg7uuxn9ssy7evfh5jq4nm79l"
    assert entry.message[0:USER_SEED_LENGTH].hex() == "7b4686f3c925f9f6571de5fa24fb6a7ac0a2e5439a48bad8ed90b6690aad6017"

    entry = entries[1]
    assert entry.label == "drt18h03w0y7qtqwtra3u4f0gu7e3kn2fslj83lqxny39m5c4rwaectswerhd2"
    assert entry.message[0:USER_SEED_LENGTH].hex() == "8928add00f0d168620a76ec7af31a92f957038a1a2ed75778a4243248d319f2f"

    entry = entries[2]
    assert entry.label == "drt1kp072dwz0arfz8m5lzmlypgu2nme9l9q33aty0znualvanfvmy5qd3yy8q"
    assert entry.message[0:USER_SEED_LENGTH].hex() == "5aa2311a2274ff47cc804f12a4e8b28cf74650a0d1efcb8175b90eda4e3e6b4c"


def test_from_text_all_for_validators():
    text = (testwallets / "validatorKey00.pem").read_text()
    entry = PemEntry.from_text_all(text)[0]
    assert entry.label == "e7beaa95b3877f47348df4dd1cb578a4f7cabf7a20bfeefe5cdd263878ff132b765e04fef6f40c93512b666c47ed7719b8902f6c922c04247989b7137e837cc81a62e54712471c97a2ddab75aa9c2f58f813ed4c0fa722bde0ab718bff382208"
    assert entry.message.hex() == "1c42aea9ae60ff04e6cac5a4c19335724f9a2e2f4a139047314fdec9f7d35e24"

    text = (testwallets / "multipleValidatorKeys.pem").read_text()
    entries = PemEntry.from_text_all(text)

    entry = entries[0]
    assert entry.label == "f8910e47cf9464777c912e6390758bb39715fffcb861b184017920e4a807b42553f2f21e7f3914b81bcf58b66a72ab16d97013ae1cff807cefc977ef8cbf116258534b9e46d19528042d16ef8374404a89b184e0a4ee18c77c49e454d04eae8d"
    assert entry.message.hex() == "7c19bf3a0c57cdd1fb08e4607cebaa3647d6b9261b4693f61e96e54b218d442a"

    entry = entries[1]
    assert entry.label == "1b4e60e6d100cdf234d3427494dac55fbac49856cadc86bcb13a01b9bb05a0d9143e86c186c948e7ae9e52427c9523102efe9019a2a9c06db02993f2e3e6756576ae5a3ec7c235d548bc79de1a6990e1120ae435cb48f7fc436c9f9098b92a0d"
    assert entry.message.hex() == "3034b1d58628a842984da0c70da0b5a251ebb2aebf51afc5b586e2839b5e5263"

    entry = entries[2]
    assert entry.label == "e5dc552b4b170cdec4405ff8f9af20313bf0e2756d06c35877b6fbcfa6b354a7b3e2d439ea87999befb09a8fa1b3f014e57ec747bf738c4199338fcd4a87b373dd62f5c8329f1f5f245956bbb06685596a2e83dc38befa63e4a2b5c4ce408506"
    assert entry.message.hex() == "de7e1b385edbb0e1e8f9fc25d91bd8eed71a1da7caab732e6b47a48042d8523d"

    entry = entries[3]
    assert entry.label == "12773304cb718250edd89770cedcbf675ccdb7fe2b30bd3185ca65ffa0d516879768ed03f92e41a6e5bc5340b78a9d02655e3b727c79730ead791fb68eaa02b84e1be92a816a9604a1ab9a6d3874b638487e2145239438a4bafac3889348d405"
    assert entry.message.hex() == "8ebeb07d296ad2529400b40687a741a135f8357f79f39fcb2894a6f9703a5816"


def test_to_text():
    text = (testwallets / "alice.pem").read_text()
    assert PemEntry.from_text_all(text)[0].to_text() == text.strip()

    text = (testwallets / "validatorKey00.pem").read_text()
    assert PemEntry.from_text_all(text)[0].to_text() == text.strip()

    text = (testwallets / "multipleUserKeys.pem").read_text()
    entries = PemEntry.from_text_all(text)
    text_actual = "\n".join([entry.to_text() for entry in entries])
    assert text_actual == text.strip()

    text = (testwallets / "multipleValidatorKeys.pem").read_text()
    entries = PemEntry.from_text_all(text)
    text_actual = "\n".join([entry.to_text() for entry in entries])
    assert text_actual == text.strip()
