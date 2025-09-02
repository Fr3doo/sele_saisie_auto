# tests/test_auth_tuple_contract.py
from sele_saisie_auto.encryption_utils import Credentials


def test_get_auth_tuple_order_and_types() -> None:
    creds = Credentials(
        aes_key=b"k", mem_key=None,
        login=b"u", mem_login=None,
        password=b"p", mem_password=None,
    )
    t = creds.get_auth_tuple()
    assert isinstance(t, tuple) and len(t) == 3
    a, u, p = t
    assert isinstance(a, bytes) and isinstance(u, bytes) and isinstance(p, bytes)
    assert (a, u, p) == (b"k", b"u", b"p")
