import builtins

from sele_saisie_auto.console_ui import ask_continue, show_separator


def test_console_utils(monkeypatch, capsys):
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda p: prompts.append(p) or "ok")
    ask_continue("continue?")
    assert prompts == ["continue?"]
    show_separator()
    assert "***" in capsys.readouterr().out
