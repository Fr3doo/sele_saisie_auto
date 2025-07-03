import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import error_handler  # noqa: E402


def test_log_error(monkeypatch):
    messages = []
    monkeypatch.setattr(
        error_handler, "write_log", lambda msg, lf, level: messages.append((msg, level))
    )
    error_handler.log_error("boom", "file")
    assert messages == [("boom", "ERROR")]


def test_log_and_raise(monkeypatch):
    messages = []
    monkeypatch.setattr(
        error_handler, "write_log", lambda msg, lf, level: messages.append(msg)
    )
    with pytest.raises(ValueError):
        error_handler.log_and_raise(ValueError("x"), "file", message="msg")
    assert messages and "msg" in messages[0]
