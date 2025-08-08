import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from configparser import ConfigParser  # noqa: E402
from multiprocessing import shared_memory  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw  # noqa: E402
from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.resources import resource_manager  # noqa: E402
from sele_saisie_auto.shared_memory_service import SharedMemoryService  # noqa: E402
from tests.conftest import FakeEncryptionService  # noqa: E402


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


class DummyResourceContext:
    def __init__(self, log_file, encryption_service=None, **kwargs):
        self.log_file = log_file
        self.encryption_service = encryption_service
        self.ctx_entered = False
        self._creds = None

    def __enter__(self):
        self.ctx_entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def get_credentials(self):
        if self._creds is None:
            self._creds = Credentials(b"k", None, b"u", None, b"p", None)
        return self._creds


def test_resource_manager_basic(monkeypatch):
    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", DummyResourceContext)

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        driver = rm.get_driver()
        creds = rm.get_credentials()

    assert driver == "driver"
    assert creds.login == b"u"


class CleanBrowserSession(DummyBrowserSession):
    sessions: list[DummyBrowserSession] = []

    def __init__(self, log_file, app_config):
        super().__init__(log_file, app_config)
        self.__class__.sessions.append(self)


class CleanResourceContext(DummyResourceContext):
    def __enter__(self):
        self.mem_key = shared_memory.SharedMemory(create=True, size=1)
        self.mem_login = shared_memory.SharedMemory(create=True, size=1)
        self.mem_password = shared_memory.SharedMemory(create=True, size=1)
        self.mem_key.buf[:1] = b"k"
        self.mem_login.buf[:1] = b"u"
        self.mem_password.buf[:1] = b"p"
        self._mems = [self.mem_key, self.mem_login, self.mem_password]
        return self

    def __exit__(self, exc_type, exc, tb):
        for mem in self._mems:
            try:
                mem.close()
                mem.unlink()
            except FileNotFoundError:
                pass

    def get_credentials(self):
        return Credentials(
            b"k",
            self.mem_key,
            b"u",
            self.mem_login,
            b"p",
            self.mem_password,
        )


def run_cleanup(monkeypatch, open_driver: bool):
    CleanBrowserSession.sessions = []
    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: CleanBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", CleanResourceContext)

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        creds = rm.get_credentials()
        driver = rm.get_driver() if open_driver else None
        names = [
            creds.mem_key.name,
            creds.mem_login.name,
            creds.mem_password.name,
        ]
    return CleanBrowserSession.sessions, rm, driver, creds, names


@pytest.mark.parametrize("open_driver, expected", [(True, "driver"), (False, None)])
def test_cleanup_returns_driver(monkeypatch, open_driver, expected):
    _, _, driver, _, _ = run_cleanup(monkeypatch, open_driver)
    assert driver == expected


def test_cleanup_returns_credentials(monkeypatch):
    _, _, _, creds, _ = run_cleanup(monkeypatch, True)
    assert creds.login == b"u"


@pytest.mark.parametrize("open_driver", [True, False])
def test_cleanup_closes_session(monkeypatch, open_driver):
    sessions, rm, _, _, _ = run_cleanup(monkeypatch, open_driver)
    assert sessions[0].closed is open_driver


@pytest.mark.parametrize("open_driver", [True, False])
def test_cleanup_session_attr_cleared(monkeypatch, open_driver):
    _, rm, _, _, _ = run_cleanup(monkeypatch, open_driver)
    assert rm._session is None


@pytest.mark.parametrize("open_driver", [True, False])
def test_cleanup_driver_attr_cleared(monkeypatch, open_driver):
    _, rm, _, _, _ = run_cleanup(monkeypatch, open_driver)
    assert rm._driver is None


def test_resource_manager_cleanup_removes_shared_memory(monkeypatch):
    _, rm, _, creds, names = run_cleanup(monkeypatch, True)
    for name in names:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)
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
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: SpyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", DummyResourceContext)

    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    rm.__enter__()
    rm.get_driver()
    rm.close()

    assert sessions[0].closed is True
    assert rm._session is None
    assert rm._driver is None


def test_resource_manager_close_is_idempotent(monkeypatch):
    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", DummyResourceContext)

    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    rm.__enter__()
    rm.get_driver()

    rm.close()
    rm.close()  # Should not raise

    assert rm._session is None
    assert rm._driver is None


class SpyConfigManager(DummyConfigManager):
    def __init__(self, log_file, calls):
        super().__init__(log_file)
        self.calls = calls

    def load(self):
        self.calls["config_loaded"] = True
        return super().load()


class SpyBrowserSession(DummyBrowserSession):
    def __init__(self, log_file, app_config, calls):
        super().__init__(log_file, app_config)
        calls["session_created"] = True
        self.calls = calls

    def open(self, url, headless=False, no_sandbox=False):
        self.calls["open_called"] = (url, headless, no_sandbox)
        return super().open(url, headless=headless, no_sandbox=no_sandbox)

    def close(self):
        self.calls["closed"] = True
        super().close()


class SpyResourceContext(DummyResourceContext):
    def __init__(self, log_file, encryption_service=None, calls=None, **kwargs):
        super().__init__(log_file, encryption_service, **kwargs)
        self.calls = calls if calls is not None else {}

    def __enter__(self):
        self.calls["ctx_enter"] = True
        return super().__enter__()

    def __exit__(self, exc_type, exc, tb):
        self.calls["ctx_exit"] = True
        return super().__exit__(exc_type, exc, tb)


@pytest.fixture()
def context_calls(monkeypatch):
    calls: dict[str, object] = {}
    monkeypatch.setattr(
        resource_manager,
        "ConfigManager",
        lambda log_file: SpyConfigManager(log_file, calls),
    )
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: SpyBrowserSession("log.html", cfg, calls),
    )
    monkeypatch.setattr(
        resource_manager,
        "ResourceContext",
        lambda log_file, encryption_service=None, **kw: SpyResourceContext(
            log_file, encryption_service, calls, **kw
        ),
    )
    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        driver = rm.get_driver()
        creds = rm.get_credentials()
    return rm, calls, driver, creds


def test_context_manager_returns_driver(context_calls):
    _, _, driver, _ = context_calls
    assert driver == "driver"


def test_context_manager_returns_credentials(context_calls):
    _, _, _, creds = context_calls
    assert creds.login == b"u"


def test_context_manager_loads_config(context_calls):
    _, calls, _, _ = context_calls
    assert calls["config_loaded"] is True


def test_context_manager_enters_context(context_calls):
    _, calls, _, _ = context_calls
    assert calls["ctx_enter"] is True


def test_context_manager_exits_context(context_calls):
    _, calls, _, _ = context_calls
    assert calls["ctx_exit"] is True


def test_context_manager_creates_session(context_calls):
    _, calls, _, _ = context_calls
    assert calls["session_created"] is True


def test_context_manager_opens_session(context_calls):
    _, calls, _, _ = context_calls
    assert calls["open_called"] == ("http://example", False, False)


def test_context_manager_closes_session(context_calls):
    _, calls, _, _ = context_calls
    assert calls["closed"] is True


def test_context_manager_clears_session(context_calls):
    rm, _, _, _ = context_calls
    assert rm._session is None


def test_context_manager_clears_driver(context_calls):
    rm, _, _, _ = context_calls
    assert rm._driver is None


def test_resource_manager_same_instances(monkeypatch):
    calls = {"open": 0, "creds": 0}

    class SpyBrowserSession(DummyBrowserSession):
        def open(self, url, headless=False, no_sandbox=False):
            calls["open"] += 1
            return object()

    class SpyResourceContext(DummyResourceContext):
        def get_credentials(self):
            if self._creds is None:
                calls["creds"] += 1
            return super().get_credentials()

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: SpyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", SpyResourceContext)

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        driver1 = rm.get_driver()
        driver2 = rm.get_driver()
        creds1 = rm.get_credentials()
        creds2 = rm.get_credentials()

    assert driver1 is driver2
    assert creds1 is creds2
    assert calls["open"] == 1
    assert calls["creds"] == 1


def test_exit_uses_shared_memory_service(monkeypatch):
    class SpySHMService:
        def __init__(self):
            self.removed = []

        def supprimer_memoire_partagee_securisee(self, mem):
            self.removed.append(mem)

        def remove_shared_memory(self, mem):
            self.supprimer_memoire_partagee_securisee(mem)

    class SpyCtx(DummyResourceContext):
        def __init__(self, log_file, encryption_service=None):
            super().__init__(log_file, encryption_service)
            self.shared_memory_service = shm_service
            self.mem_key = object()
            self.mem_login = object()
            self.mem_password = object()

        def __exit__(self, exc_type, exc, tb):
            self.shared_memory_service.remove_shared_memory(self.mem_key)
            self.shared_memory_service.remove_shared_memory(self.mem_login)
            self.shared_memory_service.remove_shared_memory(self.mem_password)

        def get_credentials(self):
            return Credentials(
                b"k",
                self.mem_key,
                b"u",
                self.mem_login,
                b"p",
                self.mem_password,
            )

    shm_service = SpySHMService()

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    enc = SpyCtx("log.html")
    monkeypatch.setattr(
        resource_manager,
        "ResourceContext",
        lambda log_file, encryption_service=None, **kw: enc,
    )

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        rm.get_credentials()

    assert shm_service.removed == [enc.mem_key, enc.mem_login, enc.mem_password]


def test_close_removes_shared_memory_segments(monkeypatch):
    class CleanResourceContext(DummyResourceContext):
        def __init__(self, log_file, encryption_service=None, **kwargs):
            super().__init__(log_file, encryption_service, **kwargs)
            self.shared_memory_service = SharedMemoryService(Logger(None))

        def __enter__(self):
            self.mem_key = shared_memory.SharedMemory(create=True, size=1)
            self.mem_login = shared_memory.SharedMemory(create=True, size=1)
            self.mem_password = shared_memory.SharedMemory(create=True, size=1)
            self.mem_key.buf[:1] = b"k"
            self.mem_login.buf[:1] = b"u"
            self.mem_password.buf[:1] = b"p"
            return self

        def get_credentials(self):
            return Credentials(
                b"k",
                self.mem_key,
                b"u",
                self.mem_login,
                b"p",
                self.mem_password,
            )

        def __exit__(self, exc_type, exc, tb):
            self.shared_memory_service.remove_shared_memory(self.mem_key)
            self.shared_memory_service.remove_shared_memory(self.mem_login)
            self.shared_memory_service.remove_shared_memory(self.mem_password)

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", CleanResourceContext)

    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    rm.__enter__()
    creds = rm.get_credentials()
    names = [
        creds.mem_key.name,
        creds.mem_login.name,
        creds.mem_password.name,
    ]
    rm.close()

    for name in names:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)

    creds.mem_key.close()
    creds.mem_login.close()
    creds.mem_password.close()


def test_context_manager_returns_self(monkeypatch):
    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", DummyResourceContext)

    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    with rm as ctx_rm:
        assert ctx_rm is rm


def test_context_manager_without_driver(monkeypatch):
    calls = {"close": 0, "open": 0}

    class SpyBrowserSession(DummyBrowserSession):
        def open(self, url, headless=False, no_sandbox=False):
            calls["open"] += 1
            return super().open(url, headless=headless, no_sandbox=no_sandbox)

        def close(self):
            calls["close"] += 1
            super().close()

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: SpyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", DummyResourceContext)

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        rm.get_credentials()  # do not open driver

    assert calls["open"] == 0
    assert calls["close"] == 0
    assert rm._session is None
    assert rm._driver is None


def test_enter_raises_runtime_error(monkeypatch):
    class FailingConfigManager(DummyConfigManager):
        def load(self):
            raise FileNotFoundError("missing")

    monkeypatch.setattr(resource_manager, "ConfigManager", FailingConfigManager)
    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    with pytest.raises(resource_manager.ResourceManagerInitError):
        with rm:
            pass


def test_no_shared_memory_left_after_close(monkeypatch):
    class CleanResourceContext(DummyResourceContext):
        def __enter__(self):
            self.mem_key = shared_memory.SharedMemory(create=True, size=1)
            self.mem_login = shared_memory.SharedMemory(create=True, size=1)
            self.mem_password = shared_memory.SharedMemory(create=True, size=1)
            self.mem_key.buf[:1] = b"k"
            self.mem_login.buf[:1] = b"u"
            self.mem_password.buf[:1] = b"p"
            return self

        def get_credentials(self):
            return Credentials(
                b"k",
                self.mem_key,
                b"u",
                self.mem_login,
                b"p",
                self.mem_password,
            )

        def __exit__(self, exc_type, exc, tb):
            for mem in (self.mem_key, self.mem_login, self.mem_password):
                try:
                    mem.close()
                    mem.unlink()
                except FileNotFoundError:
                    pass

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: DummyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", CleanResourceContext)

    rm = resource_manager.ResourceManager("log.html", FakeEncryptionService("log.html"))
    rm.__enter__()
    creds = rm.get_credentials()
    names = [creds.mem_key.name, creds.mem_login.name, creds.mem_password.name]

    rm.close()

    for name in names:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)
    # avoid ResourceWarning in CPython
    creds.mem_key.close()
    creds.mem_login.close()
    creds.mem_password.close()
