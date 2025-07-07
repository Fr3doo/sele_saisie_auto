import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from configparser import ConfigParser

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw  # noqa: E402
from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.resources import resource_manager  # noqa: E402


class DummyConfigManager:
    def __init__(self, log_file):
        self.log_file = log_file
        self.loaded = False

    def load(self):
        self.loaded = True
        cfg = ConfigParser()
        cfg["credentials"] = {"login": "enc", "mdp": "enc"}
        cfg["settings"] = {"url": "http://example"}
        return AppConfig.from_raw(AppConfigRaw(cfg))


class DummyBrowserSession:
    def __init__(self, log_file, app_config):
        self.log_file = log_file
        self.app_config = app_config
        self.closed = False

    def open(self, url, headless=False, no_sandbox=False):
        self.url = url
        return "driver"

    def close(self):
        self.closed = True


class DummyEncryption:
    def __init__(self, log_file):
        self.log_file = log_file

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def retrieve_credentials(self):
        return Credentials(b"k", None, b"u", None, b"p", None)


def test_resource_manager_basic(monkeypatch):
    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(resource_manager, "BrowserSession", DummyBrowserSession)
    monkeypatch.setattr(resource_manager, "EncryptionService", DummyEncryption)

    with resource_manager.ResourceManager("log.html") as rm:
        driver = rm.get_driver()
        creds = rm.get_credentials()

    assert driver == "driver"
    assert creds.login == b"u"
