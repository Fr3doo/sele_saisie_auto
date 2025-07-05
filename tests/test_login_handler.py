import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.login_handler import LoginHandler  # noqa: E402
from sele_saisie_auto.locators import Locators  # noqa: E402


class DummyEnc:
    def __init__(self):
        self.calls = []

    def dechiffrer_donnees(self, data, key):
        self.calls.append((data, key))
        return data.decode() if isinstance(data, bytes) else data


class DummyCreds:
    def __init__(self):
        self.login = b"user"
        self.password = b"pass"
        self.aes_key = b"key"


def test_login_calls_send_keys(monkeypatch):
    actions = []
    monkeypatch.setattr(
        "sele_saisie_auto.automation.login_handler.send_keys_to_element",
        lambda driver, by, ident, value: actions.append((ident, value)),
    )
    handler = LoginHandler("log.html")
    enc = DummyEnc()
    handler.login("driver", DummyCreds(), enc)

    assert (Locators.USERNAME.value, "user") in actions
    assert (Locators.PASSWORD.value, "pass") in actions
    assert enc.calls[0] == (b"user", b"key")
    assert enc.calls[1] == (b"pass", b"key")
