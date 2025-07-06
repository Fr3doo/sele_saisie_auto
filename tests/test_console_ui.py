import builtins

from sele_saisie_auto.console_ui import ask_continue, show_separator


def test_console_utils(monkeypatch):
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda p: prompts.append(p) or "ok")
    logged: list[str] = []
    monkeypatch.setattr(
        "sele_saisie_auto.console_ui.write_log",
        lambda msg, log_file, level="INFO", log_format="html", auto_close=False: logged.append(
            msg
        ),
    )
    ask_continue("continue?")
    assert prompts == ["continue?"]
    show_separator()
    assert any("***" in m for m in logged)
