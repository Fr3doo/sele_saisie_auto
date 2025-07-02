import runpy
import importlib
import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))




def test_import_does_not_run(monkeypatch):
    called = {}
    dummy = types.SimpleNamespace(main=lambda: called.setdefault("run", True))
    monkeypatch.setitem(sys.modules, "launcher", dummy)
    mod = importlib.import_module("main")
    importlib.reload(mod)
    assert called == {}


def test_run_as_script(monkeypatch):
    called = {}

    def fake_main():
        called["run"] = True

    dummy = types.SimpleNamespace(main=fake_main)
    monkeypatch.setitem(sys.modules, "launcher", dummy)
    runpy.run_module("main", run_name="__main__")
    assert called == {"run": True}


