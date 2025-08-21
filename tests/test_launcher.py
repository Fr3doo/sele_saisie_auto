import importlib
import sys
import types
from multiprocessing import shared_memory
from pathlib import Path
from typing import Any

import pytest

from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.memory_config import MemoryConfig

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

pytestmark = pytest.mark.slow


def import_launcher(monkeypatch):
    stub = types.SimpleNamespace(main_menu=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "sele_saisie_auto.main_menu", stub)
    return importlib.reload(importlib.import_module("sele_saisie_auto.launcher"))


class DummyMenu:
    def __init__(self):
        self.destroy_called = False

    def destroy(self):
        self.destroy_called = True


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, val):
        self.value = val


def test_cleanup_memory_segments(monkeypatch):
    launcher = import_launcher(monkeypatch)
    mem_cfg = MemoryConfig.with_uuid()
    leftovers = []
    for name in (
        mem_cfg.cle_name,
        mem_cfg.data_name,
        mem_cfg.login_name,
        mem_cfg.password_name,
    ):
        seg = shared_memory.SharedMemory(create=True, size=1, name=name)
        seg.buf[:1] = b"x"
        seg.close()
        leftovers.append(name)

    launcher.cleanup_memory_segments(mem_cfg)

    for name in leftovers:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)


class DummyEncryption:
    def __init__(self, memory_config=None):
        self.encrypted = []
        self.stored = []
        self.memory_config = memory_config or MemoryConfig()
        self.shared_memory_service = types.SimpleNamespace(
            stocker_en_memoire_partagee=lambda name, data: self.stored.append(
                (name, data)
            )
        )

    def __enter__(self):
        self.cle_aes = b"k" * 32
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stored.clear()

    def chiffrer_donnees(self, val, key):
        self.encrypted.append((val, key))
        return val.encode()

    def generer_cle_aes(self, size):
        return b"k" * size

    def store_credentials(self, login, pwd):
        self.stored.append((self.memory_config.login_name, login))
        self.stored.append((self.memory_config.password_name, pwd))


class DummyRoot:
    def __init__(self):
        self.title_value = None
        self.geometry_value = None
        self.destroy_called = False
        self.mainloop_called = False

    def title(self, val):
        self.title_value = val

    def geometry(self, val):
        self.geometry_value = val

    def destroy(self):
        self.destroy_called = True

    def mainloop(self):
        self.mainloop_called = True


class DummyStyle:
    def __init__(self, root):
        self.theme = None

    def theme_use(self, theme):
        self.theme = theme

    def configure(self, *args, **kwargs):
        pass


class DummyFrame:
    def __init__(self, *args, **kwargs):
        pass

    def columnconfigure(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass


class DummyLabelFrame(DummyFrame):
    pass


class DummyLabel:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        pass


created_vars = []


def fake_stringvar(value=""):
    var = DummyVar(value)
    created_vars.append(var)
    return var


def _parse_cli(args: list[str]):
    mod = importlib.reload(importlib.import_module("sele_saisie_auto.cli"))
    return mod.parse_args(args)


def test_parse_args_defaults(monkeypatch):
    args = _parse_cli([])
    assert args.log_level is None
    assert args.headless is False
    assert args.no_sandbox is False
    assert args.cleanup_mem is False


def test_parse_args_log_level(monkeypatch):
    args = _parse_cli(["-l", "DEBUG"])
    assert args.log_level == "DEBUG"


def test_parse_args_cleanup(monkeypatch):
    args = _parse_cli(["--cleanup-mem"])
    assert args.cleanup_mem is True


def test_run_psatime(monkeypatch, dummy_logger, sample_config):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))

    class DummyAutomation:
        def __init__(self, log_file, cfg_loaded, logger=None, services=None):
            self.called = (log_file, cfg_loaded, logger, services)
            self.resource_manager = object()
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger

    class DummyOrchestrator:
        def __init__(self, *a, **k):
            self.run_called = False
            self.run_args = None

        @classmethod
        def from_components(cls, *a, **k):
            inst = cls(*a, **k)
            return inst

        def run(self, headless=False, no_sandbox=False):
            self.run_called = True
            self.run_args = (headless, no_sandbox)

    monkeypatch.setattr(
        launcher,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    monkeypatch.setattr(
        launcher,
        "service_configurator_factory",
        lambda conf, **kw: types.SimpleNamespace(build_services=lambda lf: None),
    )
    automation_instance = {}

    def dummy_automation_factory(*args, **kwargs):
        inst = DummyAutomation(*args, **kwargs)
        automation_instance["inst"] = inst
        return inst

    monkeypatch.setattr(
        launcher.saisie_automatiser_psatime,
        "PSATimeAutomation",
        dummy_automation_factory,
    )
    orch_instance = {}
    monkeypatch.setattr(
        launcher,
        "AutomationOrchestrator",
        types.SimpleNamespace(
            from_components=lambda *a, **k: orch_instance.setdefault(
                "inst", DummyOrchestrator()
            )
        ),
    )

    launcher.run_psatime("file.html", menu, logger=dummy_logger)

    assert menu.destroy_called
    assert dummy_logger.records["info"][0].startswith("Launching")
    assert orch_instance["inst"].run_called
    assert orch_instance["inst"].run_args == (False, False)


def test_run_psatime_flags(monkeypatch, dummy_logger, sample_config):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))

    class DummyAutomation:
        def __init__(self, log_file, cfg_loaded, logger=None, services=None):
            self.resource_manager = object()
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger

    class DummyOrchestrator:
        def __init__(self):
            self.run_args = None

        @classmethod
        def from_components(cls, *a, **k):
            return cls()

        def run(self, headless=False, no_sandbox=False):
            self.run_args = (headless, no_sandbox)

    monkeypatch.setattr(
        launcher,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    monkeypatch.setattr(
        launcher,
        "service_configurator_factory",
        lambda conf, **kw: types.SimpleNamespace(build_services=lambda lf: None),
    )

    inst = DummyAutomation("file.html", app_cfg, logger=dummy_logger)
    monkeypatch.setattr(
        launcher.saisie_automatiser_psatime,
        "PSATimeAutomation",
        lambda *a, **k: inst,
    )
    orch = DummyOrchestrator()
    monkeypatch.setattr(
        launcher,
        "AutomationOrchestrator",
        types.SimpleNamespace(from_components=lambda *a, **k: orch),
    )

    launcher.run_psatime(
        "file.html",
        menu,
        logger=dummy_logger,
        headless=True,
        no_sandbox=True,
    )

    assert orch.run_args == (True, True)


def test_run_psatime_reuses_encryption_service(
    monkeypatch, dummy_logger, sample_config
):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    enc = DummyEncryption()
    enc.cle_aes = b"k" * 32

    class DummyConfigurator:
        def __init__(self, cfg, **kw):
            self.cfg = cfg

        def create_encryption_service(
            self, *a, **k
        ):  # pragma: no cover - should not be called
            raise AssertionError("should not create new encryption service")

        def create_waiter(self):
            return object()

        def create_login_handler(self, *a, **k):
            return object()

        def __getattr__(self, name):
            if name == "create_browser_session":
                return lambda log_file: object()
            raise AttributeError(name)

    monkeypatch.setattr(
        launcher,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    monkeypatch.setattr(
        launcher,
        "service_configurator_factory",
        lambda conf, **kw: DummyConfigurator(conf),
    )

    services_used = {}

    class DummyAutomation:
        def __init__(self, log_file, cfg_loaded, logger=None, services=None):
            services_used["svc"] = services
            self.resource_manager = launcher.ResourceManager(
                log_file, encryption_service=services.encryption_service
            )
            self.page_navigator = object()
            self.context = types.SimpleNamespace()
            self.logger = logger

    class DummyOrchestrator:
        def __init__(self):
            pass

        @classmethod
        def from_components(cls, *a, **k):
            return cls()

        def run(self, headless=False, no_sandbox=False):
            return None

    monkeypatch.setattr(
        launcher.saisie_automatiser_psatime,
        "PSATimeAutomation",
        DummyAutomation,
    )
    monkeypatch.setattr(
        launcher,
        "AutomationOrchestrator",
        types.SimpleNamespace(from_components=lambda *a, **k: DummyOrchestrator()),
    )

    launcher.run_psatime("file.html", menu, logger=dummy_logger, encryption_service=enc)

    assert services_used["svc"].encryption_service is enc


def test_run_psatime_with_credentials(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    enc.cle_aes = b"k" * 32
    login = DummyVar("user")
    pwd = DummyVar("pass")
    menu = DummyMenu()
    run_called = {}

    monkeypatch.setattr(
        launcher,
        "run_psatime",
        lambda lf, m, logger=None, encryption_service=None, **kw: run_called.setdefault(
            "run", (lf, kw, encryption_service)
        ),
    )
    launcher.run_psatime_with_credentials(enc, login, pwd, "log", menu, logger=None)

    assert ("memoire_nom", b"user") in enc.stored
    assert ("memoire_mdp", b"pass") in enc.stored
    assert run_called["run"] == (
        "log",
        {"headless": False, "no_sandbox": False},
        enc,
    )


def test_run_psatime_with_credentials_flags(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    enc.cle_aes = b"k" * 32
    login = DummyVar("user")
    pwd = DummyVar("pass")
    menu = DummyMenu()
    run_called = {}

    def fake_run(lf, m, logger=None, encryption_service=None, **kw):
        run_called["call"] = (lf, kw, encryption_service)

    monkeypatch.setattr(launcher, "run_psatime", fake_run)
    launcher.run_psatime_with_credentials(
        enc,
        login,
        pwd,
        "log",
        menu,
        headless=True,
        no_sandbox=True,
    )

    assert run_called["call"] == (
        "log",
        {"headless": True, "no_sandbox": True},
        enc,
    )


def test_run_psatime_with_credentials_missing(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    enc.cle_aes = b"k" * 32
    login = DummyVar("")
    pwd = DummyVar("")
    menu = DummyMenu()
    errors = []

    monkeypatch.setattr(launcher.messagebox, "showerror", lambda *a: errors.append(a))
    launcher.run_psatime_with_credentials(enc, login, pwd, "log", menu)

    assert errors
    assert not enc.stored


def test_run_psatime_with_credentials_no_key(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    enc.cle_aes = None
    login = DummyVar("user")
    pwd = DummyVar("pass")
    menu = DummyMenu()
    errors = []

    monkeypatch.setattr(launcher.messagebox, "showerror", lambda *a: errors.append(a))
    launcher.run_psatime_with_credentials(enc, login, pwd, "log", menu)

    assert errors
    assert not enc.stored


def _setup_start_configuration(monkeypatch):
    launcher = import_launcher(monkeypatch)
    created_vars.clear()
    root = DummyRoot()
    cfg = {"settings": {}}
    button: dict[str, Any] = {}
    monkeypatch.setattr(launcher.tk, "Tk", lambda: root)
    monkeypatch.setattr(launcher.tk, "StringVar", fake_stringvar)
    monkeypatch.setattr(launcher.ttk, "Style", DummyStyle)
    monkeypatch.setattr(launcher, "create_tab", lambda *a, **k: DummyFrame())
    monkeypatch.setattr(launcher, "create_a_frame", lambda *a, **k: DummyFrame())
    monkeypatch.setattr(launcher, "create_modern_label_with_grid", lambda *a, **k: None)
    monkeypatch.setattr(launcher, "create_modern_entry_with_grid", lambda *a, **k: None)
    monkeypatch.setattr(launcher, "create_combobox", lambda *a, **k: None)
    monkeypatch.setattr(launcher.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(launcher.ttk, "Label", DummyLabel)
    monkeypatch.setattr(launcher.ttk, "LabelFrame", DummyLabelFrame)

    def fake_button(frame, text, command):
        button["cmd"] = command
        return object()

    monkeypatch.setattr(launcher, "create_button_with_style", fake_button)
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: cfg)
    saved: dict[str, Any] = {}
    monkeypatch.setattr(
        launcher, "write_config_ini", lambda c, lf: saved.setdefault("cfg", c)
    )
    monkeypatch.setattr(
        launcher.messagebox, "showinfo", lambda *a: saved.setdefault("info", True)
    )
    monkeypatch.setattr(
        sys.modules["sele_saisie_auto.main_menu"],
        "main_menu",
        lambda *a, **k: (
            saved.setdefault("menu", True),
            saved.setdefault("kwargs", k),
        ),
    )
    return launcher, root, cfg, button, saved


def test_start_configuration_saves_config(monkeypatch):
    launcher, root, cfg, button, _ = _setup_start_configuration(monkeypatch)
    launcher.start_configuration(
        b"k",
        "log",
        DummyEncryption(),
        headless=True,
        no_sandbox=True,
    )
    assert root.mainloop_called
    created_vars[0].set("2024-07-01")
    created_vars[1].set("WARNING")
    button["cmd"]()
    assert cfg["settings"]["date_cible"] == "2024-07-01"
    assert cfg["settings"]["debug_mode"] == "WARNING"
    assert root.destroy_called


def test_start_configuration_calls_menu(monkeypatch):
    launcher, root, cfg, button, saved = _setup_start_configuration(monkeypatch)
    launcher.start_configuration(
        b"k",
        "log",
        DummyEncryption(),
        headless=True,
        no_sandbox=True,
    )
    button["cmd"]()
    assert saved["menu"] is True
    assert saved["kwargs"] == {"headless": True, "no_sandbox": True}


def _setup_main(monkeypatch):
    launcher = import_launcher(monkeypatch)
    dummy_args = types.SimpleNamespace(
        log_level="ERROR",
        headless=True,
        no_sandbox=True,
    )
    monkeypatch.setattr(launcher.cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(launcher, "get_log_file", lambda: "log.html")
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: {"settings": {}})
    init: dict[str, Any] = {}
    monkeypatch.setattr(
        launcher.LoggingConfigurator,
        "setup",
        lambda log_file, debug_mode, config=None: init.setdefault("lvl", debug_mode),
    )
    monkeypatch.setattr(
        launcher.multiprocessing,
        "freeze_support",
        lambda: init.setdefault("freeze", True),
    )
    monkeypatch.setattr(launcher, "EncryptionService", lambda lf: DummyEncryption())
    monkeypatch.setattr(
        sys.modules["sele_saisie_auto.main_menu"],
        "main_menu",
        lambda *a, **k: (
            init.setdefault("menu", a),
            init.setdefault("kwargs", k),
        ),
    )

    class DummyLoggerCtx:
        def __init__(self):
            self.infos: list[str] = []
            self.entered = False
            self.exited = False

        def __enter__(self):
            self.entered = True
            return self

        def __exit__(self, exc_type, exc, tb):
            self.exited = True

        def info(self, msg):
            self.infos.append(msg)

    dummy_logger = DummyLoggerCtx()
    monkeypatch.setattr(launcher, "get_logger", lambda lf: dummy_logger)
    return launcher, init, dummy_logger


def test_main_initializes(monkeypatch):
    launcher, init, dummy_logger = _setup_main(monkeypatch)
    launcher.main([])
    assert init["lvl"] == "ERROR"
    assert init["freeze"]
    assert dummy_logger.entered
    assert dummy_logger.exited


def test_main_calls_menu(monkeypatch):
    launcher, init, dummy_logger = _setup_main(monkeypatch)
    launcher.main([])
    assert init["menu"][1] == "log.html"
    assert init["kwargs"] == {"headless": True, "no_sandbox": True}


def test_main_twice_cleanup(monkeypatch):
    launcher = import_launcher(monkeypatch)

    dummy_args = types.SimpleNamespace(
        log_level=None,
        headless=False,
        no_sandbox=False,
    )
    monkeypatch.setattr(launcher.cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(launcher, "get_log_file", lambda: "log.html")
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: {"settings": {}})
    monkeypatch.setattr(launcher.LoggingConfigurator, "setup", lambda *a, **k: None)
    monkeypatch.setattr(launcher.multiprocessing, "freeze_support", lambda: None)

    mem_cfg = MemoryConfig.with_uuid()
    leftovers = []
    for name in (mem_cfg.cle_name, mem_cfg.login_name, mem_cfg.password_name):
        seg = shared_memory.SharedMemory(create=True, size=1, name=name)
        seg.buf[:1] = b"x"
        seg.close()
        leftovers.append(name)

    def enc_factory(log_file):
        return EncryptionService(log_file, memory_config=mem_cfg)

    monkeypatch.setattr(launcher, "EncryptionService", enc_factory)
    orig_cleanup = launcher.cleanup_memory_segments
    monkeypatch.setattr(
        launcher,
        "cleanup_memory_segments",
        lambda: orig_cleanup(mem_cfg),
    )

    launcher.main([])
    for name in leftovers:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)

    launcher.main([])  # second run should also succeed without errors
