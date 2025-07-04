import importlib

from sele_saisie_auto import example_plugin, plugins


def test_example_plugin_hook(capsys):
    plugins.clear()
    importlib.reload(example_plugin)
    plugins.call("before_submit", object())
    captured = capsys.readouterr()
    assert "Plugin before_submit called" in captured.out
