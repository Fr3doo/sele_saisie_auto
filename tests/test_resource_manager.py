import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from configparser import ConfigParser  # noqa: E402
from multiprocessing import shared_memory  # noqa: E402

import pytest  # noqa: E402

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


def test_resource_manager_cleanup(monkeypatch):
    sessions = []

    class CleanBrowserSession(DummyBrowserSession):
        def __init__(self, log_file, app_config):
            super().__init__(log_file, app_config)
            sessions.append(self)

    class CleanEncryption:
        def __init__(self, log_file):
            self.log_file = log_file

        def __enter__(self):
            self.mem_key = shared_memory.SharedMemory(create=True, size=1)
            self.mem_login = shared_memory.SharedMemory(create=True, size=1)
            self.mem_pwd = shared_memory.SharedMemory(create=True, size=1)
            self.mem_key.buf[:1] = b"k"
            self.mem_login.buf[:1] = b"u"
            self.mem_pwd.buf[:1] = b"p"
            self._mems = [self.mem_key, self.mem_login, self.mem_pwd]
            return self

        def __exit__(self, exc_type, exc, tb):
            for mem in self._mems:
                try:
                    mem.close()
                    mem.unlink()
                except FileNotFoundError:
                    pass

        def retrieve_credentials(self):
            return Credentials(
                b"k",
                self.mem_key,
                b"u",
                self.mem_login,
                b"p",
                self.mem_pwd,
            )

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(resource_manager, "BrowserSession", CleanBrowserSession)
    monkeypatch.setattr(resource_manager, "EncryptionService", CleanEncryption)

    with resource_manager.ResourceManager("log.html") as rm:
        creds = rm.get_credentials()
        driver = rm.get_driver()
        names = [
            creds.mem_key.name,
            creds.mem_login.name,
            creds.mem_password.name,
        ]

    assert driver == "driver"
    assert creds.login == b"u"
    assert sessions[0].closed is True
    assert rm._session is None
    assert rm._driver is None
    for name in names:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)

    # avoid ResourceWarning
    creds.mem_key.close()
    creds.mem_login.close()
    creds.mem_password.close()


def test_resource_manager_close_method(monkeypatch):
    sessions = []

    class SpyBrowserSession(DummyBrowserSession):
        def __init__(self, log_file, app_config):
            super().__init__(log_file, app_config)
            sessions.append(self)

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(resource_manager, "BrowserSession", SpyBrowserSession)
    monkeypatch.setattr(resource_manager, "EncryptionService", DummyEncryption)

    rm = resource_manager.ResourceManager("log.html")
    rm.__enter__()
    rm.get_driver()
    rm.close()

    assert sessions[0].closed is True
    assert rm._session is None
    assert rm._driver is None


def test_resource_manager_context_calls(monkeypatch):
    calls = {}

    class SpyConfigManager(DummyConfigManager):
        def load(self):
            calls["config_loaded"] = True
            return super().load()

    class SpyBrowserSession(DummyBrowserSession):
        def __init__(self, log_file, app_config):
            super().__init__(log_file, app_config)
            calls["session_created"] = True

        def open(self, url, headless=False, no_sandbox=False):
            calls["open_called"] = (url, headless, no_sandbox)
            return super().open(url, headless=headless, no_sandbox=no_sandbox)

        def close(self):
            calls["closed"] = True
            super().close()

    class SpyEncryption(DummyEncryption):
        def __enter__(self):
            calls["enc_enter"] = True
            return super().__enter__()

        def __exit__(self, exc_type, exc, tb):
            calls["enc_exit"] = True
            return super().__exit__(exc_type, exc, tb)

    monkeypatch.setattr(resource_manager, "ConfigManager", SpyConfigManager)
    monkeypatch.setattr(resource_manager, "BrowserSession", SpyBrowserSession)
    monkeypatch.setattr(resource_manager, "EncryptionService", SpyEncryption)

    with resource_manager.ResourceManager("log.html") as rm:
        driver = rm.get_driver()
        creds = rm.get_credentials()

    assert driver == "driver"
    assert creds.login == b"u"
    assert calls.get("config_loaded") is True
    assert calls.get("enc_enter") is True
    assert calls.get("enc_exit") is True
    assert calls.get("session_created") is True
    assert calls.get("open_called") == ("http://example", False, False)
    assert calls.get("closed") is True
    assert rm._session is None
    assert rm._driver is None


def test_resource_manager_same_instances(monkeypatch):
    calls = {"open": 0, "creds": 0}

    class SpyBrowserSession(DummyBrowserSession):
        def open(self, url, headless=False, no_sandbox=False):
            calls["open"] += 1
            return object()

    class SpyEncryption(DummyEncryption):
        def retrieve_credentials(self):
            calls["creds"] += 1
            return Credentials(b"k", None, b"u", None, b"p", None)

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(resource_manager, "BrowserSession", SpyBrowserSession)
    monkeypatch.setattr(resource_manager, "EncryptionService", SpyEncryption)

    with resource_manager.ResourceManager("log.html") as rm:
        driver1 = rm.get_driver()
        driver2 = rm.get_driver()
        creds1 = rm.get_credentials()
        creds2 = rm.get_credentials()

    assert driver1 is driver2
    assert creds1 is creds2
    assert calls["open"] == 1
    assert calls["creds"] == 1
