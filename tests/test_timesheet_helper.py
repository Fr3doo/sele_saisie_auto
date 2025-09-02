import sys
from pathlib import Path

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    TimeSheetContext,
    TimeSheetHelper,
)


def test_timesheethelper_run_sequence(monkeypatch):
    helper = TimeSheetHelper(TimeSheetContext("log", [], {}, {}), Logger("log"))
    seq = []
    monkeypatch.setattr(
        helper, "fill_standard_days", lambda d, j: seq.append("std") or j
    )
    monkeypatch.setattr(
        helper, "fill_work_missions", lambda d, j: seq.append("work") or j
    )
    monkeypatch.setattr(
        helper, "handle_additional_fields", lambda d: seq.append("extra")
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda *a, **k: None,
    )
    helper.run(object())
    assert seq == ["std", "work", "extra"]


def test_timesheethelper_run_early_exit(monkeypatch):
    helper = TimeSheetHelper(TimeSheetContext("log", [], {}, {}), Logger("log"))
    seq = []
    from sele_saisie_auto.constants import JOURS_SEMAINE

    all_days = list(JOURS_SEMAINE.values())

    monkeypatch.setattr(helper, "fill_standard_days", lambda d, j: all_days)
    monkeypatch.setattr(
        helper, "fill_work_missions", lambda d, j: seq.append("work") or j
    )
    monkeypatch.setattr(
        helper, "handle_additional_fields", lambda d: seq.append("extra")
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda *a, **k: None,
    )

    helper.run(object())

    assert seq == []


def test_fill_standard_days_delegates(monkeypatch):
    ctx = TimeSheetContext("log", ["desc"], {}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    helper = TimeSheetHelper(ctx, logger)

    captured = {}

    def fake_remplir(driver, items, week_days, filled, c):
        captured["args"] = (driver, items, week_days, list(filled), c)
        filled.append("lundi")
        return filled

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.remplir_jours",
        fake_remplir,
    )

    result = helper.fill_standard_days("drv", [])

    from sele_saisie_auto.constants import JOURS_SEMAINE

    assert result == ["lundi"]
    assert captured["args"] == ("drv", ["desc"], JOURS_SEMAINE, [], ctx)


def test_fill_work_missions_delegates(monkeypatch):
    work_days = {"lundi": ("desc", "8")}
    ctx = TimeSheetContext("log", [], work_days, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    helper = TimeSheetHelper(ctx, logger)

    captured = {}

    def fake_remplir(driver, wd, filled, c):
        captured["args"] = (driver, wd, list(filled), c)
        filled.append("done")
        return filled

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.remplir_mission",
        fake_remplir,
    )

    result = helper.fill_work_missions("drv", [])

    assert result == ["done"]
    assert captured["args"] == ("drv", work_days, [], ctx)


def test_handle_additional_fields_dispatch(monkeypatch):
    ctx = TimeSheetContext("log", [], {"lundi": ("En mission", "8")}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    helper = TimeSheetHelper(ctx, logger)

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.est_en_mission_presente",
        lambda wd: True,
    )
    captured = {}

    def fake_traiter(driver, fields, info, c, waiter=None):
        captured["args"] = (fields, info, c, waiter)

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.traiter_champs_mission",
        fake_traiter,
    )

    helper.handle_additional_fields("drv")

    from sele_saisie_auto.enums import MissionField

    assert captured["args"] == (
        list(MissionField),
        ctx.project_mission_info,
        ctx,
        helper.waiter,
    )


def test_handle_additional_fields_no_mission(monkeypatch):
    ctx = TimeSheetContext("log", [], {}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    helper = TimeSheetHelper(ctx, logger)

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.est_en_mission_presente",
        lambda wd: False,
    )
    called = {}

    def fake_traiter(*_a, **_k):
        called["called"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.traiter_champs_mission",
        fake_traiter,
    )

    helper.handle_additional_fields("drv")

    assert "called" not in called


def test_run_logs_early_return(monkeypatch):
    ctx = TimeSheetContext("log", [], {}, {})
    logs: list[tuple[str, str]] = []
    logger = Logger(
        "log",
        writer=lambda msg, _lf, level="INFO", **_k: logs.append((level, msg)),
    )
    helper = TimeSheetHelper(ctx, logger)

    from sele_saisie_auto.constants import JOURS_SEMAINE

    all_days = list(JOURS_SEMAINE.values())
    monkeypatch.setattr(helper, "fill_standard_days", lambda d, j: all_days)
    work_called = {"called": False}
    monkeypatch.setattr(
        helper,
        "fill_work_missions",
        lambda *_a, **_k: work_called.__setitem__("called", True),
    )
    extra_called = {"called": False}
    monkeypatch.setattr(
        helper,
        "handle_additional_fields",
        lambda *_a, **_k: extra_called.__setitem__("called", True),
    )

    helper.run(object())

    assert ("INFO", messages.TIMESHEET_ALREADY_COMPLETE) in logs
    assert not work_called["called"]
    assert not extra_called["called"]
