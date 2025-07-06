import sys
from pathlib import Path

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.utils.misc import program_break_time  # noqa: E402


def test_program_break_time_executes(monkeypatch, capsys):
    calls = []

    def fake_sleep(seconds: int) -> None:
        assert seconds == 1
        calls.append(seconds)

    monkeypatch.setattr("sele_saisie_auto.utils.misc.time.sleep", fake_sleep)

    program_break_time(3, "Attente")

    assert len(calls) == 3
    output = capsys.readouterr().out
    assert "Attente 3 secondes" in output
    assert output.count(".") == 3
