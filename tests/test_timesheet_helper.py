import sys
from pathlib import Path

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    TimeSheetContext,
    TimeSheetHelper,
    remplir_jours,
    remplir_mission,
)


def test_remplir_jours_collects_filled_days(monkeypatch):
    liste_items = ["desc1"]
    jours_semaine = {1: "lundi", 2: "mardi"}
    jours_remplis = []

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
    result = remplir_jours(None, liste_items, jours_semaine, jours_remplis, ctx)
    assert result == ["lundi"]


def test_remplir_mission_calls_helpers(monkeypatch):
    jours_de_travail = {
        "lundi": ("desc1", "8"),
        "mardi": ("En mission", "8"),
    }
    jours_remplis = []
    calls = {"traiter": [], "specifique": []}

    def fake_traiter(driver, jour, desc, val, jours, ctx):
        calls["traiter"].append((jour, desc, val))
        jours.append(jour)
        return jours

    def fake_specifique(driver, jour, val, jours, ctx):
        calls["specifique"].append((jour, val))
        jours.append(f"mission_{jour}")

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.traiter_jour", fake_traiter
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_mission_specifique",
        fake_specifique,
    )

    ctx = TimeSheetContext("log", [], {}, {})
    result = remplir_mission(None, jours_de_travail, jours_remplis, ctx)

    assert result == ["lundi", "mission_mardi"]
    assert calls["traiter"] == [("lundi", "desc1", "8")]
    assert calls["specifique"] == [("mardi", "8")]


def test_timesheethelper_run_sequence(monkeypatch):
    helper = TimeSheetHelper(TimeSheetContext("log", [], {}, {}))
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
    helper.run(None)
    assert seq == ["std", "work", "extra"]
