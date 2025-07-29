import passuth
from hypothesis import example, given, settings
from hypothesis import strategies as st


@given(text=st.text(max_size=1_000_000))
@example(text="🐍👍")
@example(text="따이タイ泰伊TàiтайتايΤαϊ")  # noqa: RUF001
@settings(deadline=1000, max_examples=30)
def test_generate_hash_str(text: str):
    texte = text.encode()
    hash_value = passuth.generate_hash(text)
    hash_value2 = passuth.generate_hash(texte)

    assert isinstance(hash_value, str)
    assert passuth.verify_password(text, hash_value)
    assert passuth.verify_password(texte, hash_value)
    assert passuth.verify_password(text, hash_value2)


@given(binary=st.binary(max_size=1_000_000))
@example(binary="🐍👍".encode())
@settings(deadline=1000, max_examples=30)
def test_generate_hash_bytes(binary: bytes):
    ba = bytearray(binary)
    mv = memoryview(binary)
    hash_value = passuth.generate_hash(binary)
    hash_value2 = passuth.generate_hash(ba)
    _ = passuth.generate_hash(mv)

    assert isinstance(hash_value, str)
    assert passuth.verify_password(binary, hash_value)
    assert passuth.verify_password(ba, hash_value)
    assert passuth.verify_password(mv, hash_value)
    assert passuth.verify_password(binary, hash_value2)


def test_verify_password():
    values = [
        "$argon2i$v=19$m=16,t=2,p=1$ZVZWeGtzNVZqeExTVzNSOA$fx0EYEB1zO8i+J2H+OFI4w",
        "$argon2d$v=19$m=16,t=2,p=1$Mmx3eWR3YkJONkhoTGFnNA$HD1EIj2bqdfwQrJDP+FY6w",
        "$argon2id$v=19$m=16,t=2,p=1$UmtRRmdBRU53QlptNk8ycw$UyyArpJ8yasrc93GImQjFQ",
        "$scrypt$ln=16,r=8,p=1$aM15713r3Xsvxbi31lqr1Q$nFNh2CVHVjNldFVKDHDlm4CbdRSCdEBsjjJxD+iCs5E",
    ]

    for value in values:
        assert passuth.verify_password("password", value)


def test_version():
    assert isinstance(passuth.__version__, str)
    assert passuth.__version__ != "unknown"
