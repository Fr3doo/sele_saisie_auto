import sys
from pathlib import Path

import pytest

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.utils.misc import program_break_time  # noqa: E402


@pytest.mark.parametrize("delay", [0, 1, 3])
def test_program_break_time_executes(monkeypatch, delay):
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

    program_break_time(delay, "Attente")

    assert calls == [1] * delay
    assert any(msg.startswith(f"Attente {delay} secondes") for msg in logged)
    assert logged.count(".") == delay
