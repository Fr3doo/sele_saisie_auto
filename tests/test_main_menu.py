import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))




class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, val):
        self.value = val


class DummyEntry:
    def __init__(self):
        self.focus_called = False

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def focus(self):
        self.focus_called = True


class DummyButton:
    def __init__(self, command=None):
        self.command = command
        self.binds = []
        self.pack_kwargs = None

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs

    def bind(self, event, func):
        self.binds.append((event, func))

    def invoke(self):
        if self.command:
            self.command()


class DummyFrame:
    def __init__(self):
        self.pack_kwargs = None

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs


class DummyLabel:
    def __init__(self, *args, **kwargs):
        self.pack_args = None

    def pack(self, **kwargs):
        self.pack_args = kwargs


class DummyTk:
    def __init__(self):
        self.destroy_called = False
        self.title_value = None
        self.resizable_value = None
        self.geometry_value = None
        self.mainloop_called = False

    def title(self, val):
        self.title_value = val

    def resizable(self, x, y):
        self.resizable_value = (x, y)

    def geometry(self, val):
        self.geometry_value = val

    def mainloop(self):
        self.mainloop_called = True

    def destroy(self):
        self.destroy_called = True


# holders for created objects
created_vars = []
created_entries = []
created_buttons = []


def fake_stringvar(value=""):
    var = DummyVar(value)
    created_vars.append(var)
    return var


def fake_create_button_without_style(frame, text, command, **kwargs):
    btn = DummyButton(command)
    btn.text = text
    created_buttons.append(btn)
    return btn


def fake_create_labeled_frame(*args, **kwargs):
    return DummyFrame()


def fake_create_entry(*args, **kwargs):
    entry = DummyEntry()
    created_entries.append(entry)
    return entry


# Tests

def test_main_menu_builds_and_commands(monkeypatch):
    created_vars.clear()
    created_entries.clear()
    created_buttons.clear()

    dummy_launcher = types.SimpleNamespace(
        run_psatime_with_credentials=lambda *a, **k: None,
        start_configuration=lambda *a, **k: None,
    )
    monkeypatch.setitem(sys.modules, "launcher", dummy_launcher)
    import importlib
    main_menu = importlib.import_module("main_menu")

    monkeypatch.setattr(
        main_menu,
        "tk",
        types.SimpleNamespace(Tk=DummyTk, StringVar=fake_stringvar, Label=DummyLabel),
    )
    monkeypatch.setattr(main_menu, "create_button_without_style", fake_create_button_without_style)
    monkeypatch.setattr(main_menu, "create_labeled_frame", fake_create_labeled_frame)
    monkeypatch.setattr(main_menu, "create_Modern_entry_with_grid", fake_create_entry)
    monkeypatch.setattr(main_menu, "create_Modern_entry_with_grid_for_password", fake_create_entry)
    monkeypatch.setattr(main_menu, "create_Modern_label_with_grid", lambda *a, **k: DummyLabel())

    run_calls = {}

    def fake_run_psa(enc_service, key, login_var, pwd_var, log_file, menu):
        run_calls["login"] = login_var.get()
        run_calls["pwd"] = pwd_var.get()
        run_calls["destroyed"] = menu.destroy_called

    monkeypatch.setattr(main_menu, "run_psatime_with_credentials", fake_run_psa)

    config_calls = {}

    def fake_start_config(key, log, enc):
        config_calls["called"] = True

    monkeypatch.setattr(main_menu, "start_configuration", fake_start_config)

    main_menu.main_menu(b"k", "log.html", object())

    assert created_entries[0].focus_called
    assert created_buttons[0].text == "Lancer votre PSATime"
    assert created_buttons[1].text == "Configurer le lancement"

    created_buttons[0].invoke()
    assert run_calls == {"login": "", "pwd": "", "destroyed": False}

    created_buttons[1].invoke()
    assert config_calls == {"called": True}
    assert created_buttons[1].command is not None
