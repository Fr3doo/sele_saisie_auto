import importlib
import sys
import types
from pathlib import Path

import pytest

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
    def __init__(self):
        self.encrypted = []
        self.stored = []
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
        self.stored.append(("memoire_nom", login))
        self.stored.append(("memoire_mdp", pwd))


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

    args = mod.parse_args(["-l", "DEBUG"])
    assert args.log_level == "DEBUG"


def test_run_psatime(monkeypatch, dummy_logger):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    calls = {}

    fake_mod = types.SimpleNamespace(main=lambda lf: calls.setdefault("main", lf))
    monkeypatch.setitem(
        sys.modules, "sele_saisie_auto.saisie_automatiser_psatime", fake_mod
    )
    monkeypatch.setattr(launcher, "saisie_automatiser_psatime", fake_mod)

    launcher.run_psatime("file.html", menu, logger=dummy_logger)

    assert menu.destroy_called
    assert dummy_logger.records["info"][0].startswith("Launching")
    assert calls["main"] == "file.html"


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
        lambda lf, m, logger=None: run_called.setdefault("run", lf),
    )
    launcher.run_psatime_with_credentials(enc, login, pwd, "log", menu, logger=None)

    assert ("memoire_nom", b"user") in enc.stored
    assert ("memoire_mdp", b"pass") in enc.stored
    assert run_called["run"] == "log"


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
        launcher, "main_menu", lambda *a, **k: saved.setdefault("menu", True)
    )

    launcher.start_configuration(b"k", "log", DummyEncryption())

    assert root.mainloop_called
    created_vars[0].set("2024-07-01")
    created_vars[1].set("WARNING")
    button["cmd"]()

    assert cfg["settings"]["date_cible"] == "2024-07-01"
    assert cfg["settings"]["debug_mode"] == "WARNING"
    assert root.destroy_called
    assert saved["menu"] is True


def test_main(monkeypatch):
    launcher = import_launcher(monkeypatch)
    dummy_args = types.SimpleNamespace(log_level="ERROR")
    monkeypatch.setattr(launcher.cli, "parse_args", lambda argv: dummy_args)
    monkeypatch.setattr(launcher, "get_log_file", lambda: "log.html")
    cfg = {"settings": {}}
    monkeypatch.setattr(launcher, "read_config_ini", lambda lf: cfg)
    init = {}
    monkeypatch.setattr(
        launcher,
        "initialize_logger",
        lambda c, log_level_override=None: init.setdefault("lvl", log_level_override),
    )
    monkeypatch.setattr(
        launcher.multiprocessing,
        "freeze_support",
        lambda: init.setdefault("freeze", True),
    )
    enc = DummyEncryption()
    monkeypatch.setattr(launcher, "EncryptionService", lambda lf: enc)
    monkeypatch.setattr(launcher, "main_menu", lambda *a: init.setdefault("menu", a))
    monkeypatch.setattr(launcher, "close_logs", lambda lf: init.setdefault("close", lf))

    launcher.main([])

    assert init["lvl"] == "ERROR"
    assert init["freeze"]
    assert init["menu"][1] == "log.html"
    assert init["close"] == "log.html"
