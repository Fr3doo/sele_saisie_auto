import importlib
import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402


def import_launcher(monkeypatch):
    stub = types.SimpleNamespace(main_menu=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "main_menu", stub)
    return importlib.reload(importlib.import_module("launcher"))


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

    def chiffrer_donnees(self, val, key):
        self.encrypted.append((val, key))
        return val.encode()

    def stocker_en_memoire_partagee(self, name, data):
        self.stored.append((name, data))

    def generer_cle_aes(self, size):
        return b"k" * size


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
    launcher = import_launcher(monkeypatch)
    args = launcher.parse_args([])
    assert args.log_level is None

    args = launcher.parse_args(["-l", "DEBUG"])
    assert args.log_level == "DEBUG"


def test_run_psatime(monkeypatch):
    launcher = import_launcher(monkeypatch)
    menu = DummyMenu()
    calls = {}

    def fake_write_log(msg, lf, level):
        calls["log"] = (msg, lf, level)

    fake_mod = types.SimpleNamespace(main=lambda lf: calls.setdefault("main", lf))
    monkeypatch.setitem(sys.modules, "saisie_automatiser_psatime", fake_mod)
    monkeypatch.setattr(launcher, "write_log", fake_write_log)

    launcher.run_psatime("file.html", menu)

    assert menu.destroy_called
    assert calls["log"][0].startswith("Launching")
    assert calls["main"] == "file.html"


def test_run_psatime_with_credentials(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    login = DummyVar("user")
    pwd = DummyVar("pass")
    menu = DummyMenu()
    run_called = {}

    monkeypatch.setattr(
        launcher, "run_psatime", lambda lf, m: run_called.setdefault("run", lf)
    )
    launcher.run_psatime_with_credentials(enc, b"k", login, pwd, "log", menu)

    assert ("memoire_nom", b"user") in enc.stored
    assert ("memoire_mdp", b"pass") in enc.stored
    assert run_called["run"] == "log"


def test_run_psatime_with_credentials_missing(monkeypatch):
    launcher = import_launcher(monkeypatch)
    enc = DummyEncryption()
    login = DummyVar("")
    pwd = DummyVar("")
    menu = DummyMenu()
    errors = []

    monkeypatch.setattr(launcher.messagebox, "showerror", lambda *a: errors.append(a))
    launcher.run_psatime_with_credentials(enc, b"k", login, pwd, "log", menu)

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
    monkeypatch.setattr(launcher, "create_Modern_label_with_pack", lambda *a, **k: None)
    monkeypatch.setattr(launcher, "create_Modern_entry_with_pack", lambda *a, **k: None)
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
    monkeypatch.setattr(launcher, "parse_args", lambda argv: dummy_args)
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
