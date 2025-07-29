import passuth
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

argon2_available = True
try:
    from argon2 import PasswordHasher
except ImportError:
    from unittest.mock import Mock

    argon2_available = False
    PasswordHasher = Mock()  # for type checking


pytestmark = pytest.mark.skipif(
    not argon2_available,
    reason="argon2_cffi is not installed, skipping tests",
)


@given(text=st.text(max_size=1000))
@settings(deadline=1000, max_examples=30)
def test_argon2_to_passuth(text: str):
    ph = PasswordHasher()
    hash_value = ph.hash(text)
    assert passuth.verify_password(text, hash_value)


@given(text=st.text(max_size=1000))
@settings(deadline=1000, max_examples=30)
def test_passuth_to_argon2(text: str):
    ph = PasswordHasher()
    hash_value = passuth.generate_hash(text)
    assert ph.verify(hash_value, text)
