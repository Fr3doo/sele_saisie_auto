import importlib
import runpy
import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


def test_import_does_not_run(monkeypatch):
    called = {}
    dummy = types.SimpleNamespace(main=lambda: called.setdefault("run", True))
    monkeypatch.setitem(sys.modules, "sele_saisie_auto.launcher", dummy)
    mod = importlib.import_module("sele_saisie_auto.main")
    importlib.reload(mod)
    assert called == {}
    sys.modules.pop("sele_saisie_auto.main", None)


def test_run_as_script(monkeypatch):
    called = {}

    def fake_main():
        called["run"] = True

    dummy = types.SimpleNamespace(main=fake_main)
    monkeypatch.setitem(sys.modules, "sele_saisie_auto.launcher", dummy)
    sys.modules.pop("sele_saisie_auto.main", None)
    runpy.run_module("sele_saisie_auto.main", run_name="__main__")
    assert called == {"run": True}
