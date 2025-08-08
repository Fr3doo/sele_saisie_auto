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


@pytest.fixture
def cleanup_setup(monkeypatch):
    """Create a ResourceManager with shared memory segments for cleanup tests."""
    sessions: list[DummyBrowserSession] = []

    class CleanBrowserSession(DummyBrowserSession):
        def __init__(self, log_file, app_config):
            super().__init__(log_file, app_config)
            sessions.append(self)

    class CleanResourceContext(DummyResourceContext):
        def __enter__(self):
            self.mem_key = shared_memory.SharedMemory(create=True, size=1)
            self.mem_login = shared_memory.SharedMemory(create=True, size=1)
            self.mem_pwd = shared_memory.SharedMemory(create=True, size=1)
            self.mem_key.buf[:1] = b"k"
            self.mem_login.buf[:1] = b"u"
            self.mem_pwd.buf[:1] = b"p"
            return self

        def __exit__(self, exc_type, exc, tb):
            for mem in (self.mem_key, self.mem_login, self.mem_pwd):
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
                self.mem_pwd,
            )

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
        driver = rm.get_driver()
        creds = rm.get_credentials()
        names = [
            creds.mem_key.name,
            creds.mem_login.name,
            creds.mem_password.name,
        ]

    yield sessions[0], rm, driver, creds, names

    creds.mem_key.close()
    creds.mem_login.close()
    creds.mem_password.close()


@pytest.fixture
def context_calls_setup(monkeypatch):
    """Run ResourceManager and record internal call events."""
    calls: dict[str, object] = {}

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

    class SpyResourceContext(DummyResourceContext):
        def __enter__(self):
            calls["ctx_enter"] = True
            return super().__enter__()

        def __exit__(self, exc_type, exc, tb):
            calls["ctx_exit"] = True
            return super().__exit__(exc_type, exc, tb)

    monkeypatch.setattr(resource_manager, "ConfigManager", SpyConfigManager)
    monkeypatch.setattr(
        resource_manager,
        "create_session",
        lambda cfg: SpyBrowserSession("log.html", cfg),
    )
    monkeypatch.setattr(resource_manager, "ResourceContext", SpyResourceContext)

    with resource_manager.ResourceManager(
        "log.html", FakeEncryptionService("log.html")
    ) as rm:
        rm.get_driver()
        rm.get_credentials()

    return calls, rm


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


def test_cleanup_returns_driver(cleanup_setup):
    _, _, driver, _, _ = cleanup_setup
    assert driver == "driver"


def test_cleanup_returns_credentials(cleanup_setup):
    _, _, _, creds, _ = cleanup_setup
    assert creds.login == b"u"


def test_cleanup_closes_session(cleanup_setup):
    session, _, _, _, _ = cleanup_setup
    assert session.closed is True


def test_cleanup_clears_session_attribute(cleanup_setup):
    _, rm, _, _, _ = cleanup_setup
    assert rm._session is None


def test_cleanup_clears_driver_attribute(cleanup_setup):
    _, rm, _, _, _ = cleanup_setup
    assert rm._driver is None


@pytest.mark.parametrize("index", [0, 1, 2])
def test_cleanup_removes_shared_memory_segments(cleanup_setup, index):
    _, _, _, _, names = cleanup_setup
    with pytest.raises(FileNotFoundError):
        shared_memory.SharedMemory(name=names[index])


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


@pytest.mark.parametrize(
    "key,expected",
    [
        ("config_loaded", True),
        ("ctx_enter", True),
        ("ctx_exit", True),
        ("session_created", True),
        ("open_called", ("http://example", False, False)),
        ("closed", True),
    ],
)
def test_resource_manager_context_calls(key, expected, context_calls_setup):
    calls, _ = context_calls_setup
    assert calls.get(key) == expected


def test_context_calls_session_cleared(context_calls_setup):
    _, rm = context_calls_setup
    assert rm._session is None


def test_context_calls_driver_cleared(context_calls_setup):
    _, rm = context_calls_setup
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
