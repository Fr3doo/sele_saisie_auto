import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.day_filler import DayFiller  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    TimeSheetContext,
    remplir_jours,
    remplir_mission,
)


def test_remplir_jours_collects_filled_days(monkeypatch):
    liste_items = ["desc1"]
    week_days = {1: "lundi", 2: "mardi"}
    filled_days: list[str] = []

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda driver, desc, id_value: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda driver, by, locator, timeout: object(),
    )

    def fake_verifier(element, day_label):
        return day_label if day_label == "lundi" else None

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.verifier_champ_jour_rempli",
        fake_verifier,
    )

    ctx = TimeSheetContext("log", liste_items, {}, {})
    result = remplir_jours(None, liste_items, week_days, filled_days, ctx)
    assert result == ["lundi"]


def test_remplir_mission_calls_helpers(monkeypatch):
    work_days = {
        "lundi": ("desc1", "8"),
        "mardi": ("En mission", "8"),
    }
    filled_days: list[str] = []
    calls = {"traiter": [], "specifique": []}

    def fake_traiter(self, driver, jour, desc, val, jours):
        calls["traiter"].append((jour, desc, val))
        jours.append(jour)
        return jours

    def fake_specifique(self, driver, jour, val, jours):
        calls["specifique"].append((jour, val))
        jours.append(f"mission_{jour}")

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.DayFiller.traiter_jour", fake_traiter
    )
    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.DayFiller.remplir_mission_specifique",
        fake_specifique,
    )

    ctx = TimeSheetContext("log", [], {}, {})
    result = remplir_mission(None, work_days, filled_days, ctx)

    assert result == ["lundi", "mission_mardi"]
    assert calls["traiter"] == [("lundi", "desc1", "8")]
    assert calls["specifique"] == [("mardi", "8")]


class DummyWaiter:
    def wait_until_dom_is_stable(self, *a, **k):
        pass

    def wait_for_dom_ready(self, *a, **k):
        pass

    def wait_for_element(self, *a, **k):
        return None


def test_fill_standard_days_delegates(monkeypatch):
    ctx = TimeSheetContext("log", ["desc"], {}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    filler = DayFiller(ctx, logger, DummyWaiter())

    captured = {}

    def fake_remplir(driver, items, week_days, filled, c):
        captured["args"] = (driver, items, week_days, list(filled), c)
        filled.append("lundi")
        return filled

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.remplir_jours",
        fake_remplir,
    )

    result = filler.fill_standard_days("drv", [])

    from sele_saisie_auto.constants import JOURS_SEMAINE

    assert result == ["lundi"]
    assert captured["args"] == ("drv", ["desc"], JOURS_SEMAINE, [], ctx)


def test_fill_work_missions_delegates(monkeypatch):
    work_days = {"lundi": ("desc", "8")}
    ctx = TimeSheetContext("log", [], work_days, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    filler = DayFiller(ctx, logger, DummyWaiter())

    captured = {}

    def fake_remplir(driver, wd, filled, c):
        captured["args"] = (driver, wd, list(filled), c)
        filled.append("done")
        return filled

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.remplir_mission",
        fake_remplir,
    )

    result = filler.fill_work_missions("drv", [])

    assert result == ["done"]
    assert captured["args"] == ("drv", work_days, [], ctx)


def test_handle_additional_fields_dispatch(monkeypatch):
    ctx = TimeSheetContext("log", [], {"lundi": ("En mission", "8")}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    filler = DayFiller(ctx, logger, DummyWaiter())

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.est_en_mission_presente",
        lambda wd: True,
    )
    captured = {}

    def fake_traiter(driver, ids, mapping, info, c, waiter=None):
        captured["args"] = (ids, mapping, info, c, waiter)

    monkeypatch.setattr(
        "sele_saisie_auto.day_filler.traiter_champs_mission",
        fake_traiter,
    )

    filler.handle_additional_fields("drv")

    from sele_saisie_auto.constants import (
        ID_TO_KEY_MAPPING,
        LISTES_ID_INFORMATIONS_MISSION,
    )

    assert captured["args"] == (
        LISTES_ID_INFORMATIONS_MISSION,
        ID_TO_KEY_MAPPING,
        ctx.project_mission_info,
        ctx,
        filler.waiter,
    )


def test_handle_additional_fields_no_mission(monkeypatch):
    ctx = TimeSheetContext("log", [], {}, {})
    logger = Logger("log", writer=lambda *a, **k: None)
    filler = DayFiller(ctx, logger, DummyWaiter())

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

    filler.handle_additional_fields("drv")

    assert "called" not in called
