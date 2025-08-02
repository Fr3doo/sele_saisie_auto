import importlib
import sys
import types
from multiprocessing import shared_memory
from pathlib import Path

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


created_vars = []


def fake_stringvar(value=""):
    var = DummyVar(value)
    created_vars.append(var)
    return var


def test_parse_args_basic(monkeypatch):
    mod = importlib.reload(importlib.import_module("sele_saisie_auto.cli"))
    args = mod.parse_args([])
    assert args.log_level is None
    assert args.headless is False
    assert args.no_sandbox is False
    assert args.cleanup_mem is False

    args = mod.parse_args(["-l", "DEBUG"])
    assert args.log_level == "DEBUG"

    args = mod.parse_args(["--cleanup-mem"])
    assert args.cleanup_mem is True


def test_run_psatime(monkeypatch, dummy_logger, sample_config):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))

    class DummyAutomation:
        def __init__(self, log_file, cfg_loaded, logger=None):
            self.called = (log_file, cfg_loaded, logger)
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
        def __init__(self, log_file, cfg_loaded, logger=None):
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
        lambda lf, m, logger=None, **kw: run_called.setdefault("run", (lf, kw)),
    )
    launcher.run_psatime_with_credentials(enc, login, pwd, "log", menu, logger=None)

    assert ("memoire_nom", b"user") in enc.stored
    assert ("memoire_mdp", b"pass") in enc.stored
    assert run_called["run"] == ("log", {"headless": False, "no_sandbox": False})


def test_run_psatime_with_credentials_flags(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    enc.cle_aes = b"k" * 32
    login = DummyVar("user")
    pwd = DummyVar("pass")
    menu = DummyMenu()
    run_called = {}

    def fake_run(lf, m, logger=None, **kw):
        run_called["call"] = (lf, kw)

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

    assert run_called["call"] == ("log", {"headless": True, "no_sandbox": True})


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


def test_start_configuration_and_save(monkeypatch):
    launcher = import_launcher(monkeypatch)
    created_vars.clear()
    root = DummyRoot()
    cfg = {"settings": {}}
    button = {}

    monkeypatch.setattr(launcher.tk, "Tk", lambda: root)
    monkeypatch.setattr(launcher.tk, "StringVar", fake_stringvar)
    monkeypatch.setattr(launcher.ttk, "Style", DummyStyle)
    monkeypatch.setattr(launcher, "create_tab", lambda *a, **k: object())
    monkeypatch.setattr(launcher, "create_a_frame", lambda *a, **k: object())
    monkeypatch.setattr(launcher, "create_modern_label_with_pack", lambda *a, **k: None)
    monkeypatch.setattr(launcher, "create_modern_entry_with_pack", lambda *a, **k: None)
    monkeypatch.setattr(launcher, "create_combobox_with_pack", lambda *a, **k: None)

    def fake_button(frame, text, command):
        button["cmd"] = command
        return object()

    monkeypatch.setattr(launcher, "create_button_with_style", fake_button)
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: cfg)
    saved = {}
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
    assert saved["menu"] is True
    assert saved["kwargs"] == {"headless": True, "no_sandbox": True}


def test_main(monkeypatch):
    launcher = import_launcher(monkeypatch)
    dummy_args = types.SimpleNamespace(
        log_level="ERROR",
        headless=True,
        no_sandbox=True,
    )
    monkeypatch.setattr(launcher.cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(launcher, "get_log_file", lambda: "log.html")
    cfg = {"settings": {}}
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: cfg)
    init = {}
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
    enc = DummyEncryption()
    monkeypatch.setattr(launcher, "EncryptionService", lambda lf: enc)
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
            self.infos = []
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

    launcher.main([])

    assert init["lvl"] == "ERROR"
    assert init["freeze"]
    assert init["menu"][1] == "log.html"
    assert init["kwargs"] == {"headless": True, "no_sandbox": True}
    assert dummy_logger.entered and dummy_logger.exited


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
