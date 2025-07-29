import types

from sele_saisie_auto.utils import misc as utils_misc


def test_clear_screen_logs_error(monkeypatch):
    logs = []
    monkeypatch.setattr(
        utils_misc, "os", types.SimpleNamespace(name="posix"), raising=False
    )
    monkeypatch.setattr(
        utils_misc.subprocess,
        "run",
        lambda *a, **k: types.SimpleNamespace(returncode=1),
    )
    monkeypatch.setattr(utils_misc.shared_utils, "get_log_file", lambda: "log.html")
    monkeypatch.setattr(
        utils_misc,
        "write_log",
        lambda msg, log_file, level="INFO", log_format="html", auto_close=False: logs.append(
            (msg, level)
        ),
    )
    utils_misc.clear_screen()
    assert logs and logs[0][1] == "ERROR"
