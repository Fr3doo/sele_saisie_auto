import builtins

import sele_saisie_auto.logger_utils as logger_utils
from sele_saisie_auto import console_ui
from sele_saisie_auto.console_ui import ask_continue, show_separator


def test_console_ui_basic(monkeypatch):
    prompts: list[str] = []
    monkeypatch.setattr(builtins, "input", lambda p: prompts.append(p) or "ok")

    printed: list[str] = []

    def fake_print(*args, **kwargs):
        printed.append(" ".join(str(a) for a in args))

    monkeypatch.setattr(builtins, "print", fake_print)
    monkeypatch.setattr(
        "sele_saisie_auto.logger_utils.write_log", lambda msg, *a, **k: fake_print(msg)
    )

    ask_continue("continue?")
    assert prompts == ["continue?"]

    show_separator()
    assert any("***" in msg for msg in printed)
