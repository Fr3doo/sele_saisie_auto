import importlib

from examples import example_plugin
from sele_saisie_auto import plugins


def test_example_plugin_hook(monkeypatch):
    plugins.clear()
    importlib.reload(example_plugin)
    logged: list[str] = []
    monkeypatch.setattr(
        "examples.example_plugin.write_log",
        lambda msg, log_file, level="INFO", log_format="html", auto_close=False: logged.append(
            msg
        ),
    )
    plugins.call("before_submit", object())
    assert any("Plugin before_submit called" in msg for msg in logged)
