import sys
from pathlib import Path

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.utils.misc import program_break_time  # noqa: E402


def test_program_break_time_executes(monkeypatch):
    calls = []
    logged: list[str] = []

    def fake_sleep(seconds: int) -> None:
        assert seconds == 1
        calls.append(seconds)

    monkeypatch.setattr("sele_saisie_auto.utils.misc.time.sleep", fake_sleep)
    monkeypatch.setattr(
        "sele_saisie_auto.utils.misc.write_log",
        lambda msg, log_file, level="INFO", log_format="html", auto_close=False: logged.append(
            msg
        ),
    )

    program_break_time(3, "Attente")

    assert calls == [1, 1, 1]
    assert any(msg.startswith("Attente 3 secondes") for msg in logged)
    assert logged.count(".") == 3
