import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

pytestmark = pytest.mark.slow

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    TimeSheetContext,
    initialize,
    main,
    remplir_mission_specifique,
    traiter_champs_mission,
    traiter_jour,
)


def test_traiter_jour_paths(monkeypatch):
    # already filled
    ctx = TimeSheetContext("log", [], {}, {})
    assert traiter_jour(None, "lundi", "desc", "8", ["lundi"], ctx) == ["lundi"]

    # row not found
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: None,
    )
    result = traiter_jour(None, "lundi", "desc", "8", [], ctx)
    assert result == []

    # value already correct
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    calls = {}
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.afficher_message_insertion",
        lambda *a: calls.setdefault("afficher", []).append(a),
    )
    result = traiter_jour(None, "lundi", "desc", "8", [], ctx)
    assert result == ["lundi"]
    assert calls["afficher"]

    # need insertion
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: calls.setdefault("effacer", True),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: True,
    )
    result = traiter_jour(None, "mardi", "desc", "8", [], ctx)
    assert "mardi" in result
    assert calls["effacer"]


def test_remplir_mission_specifique(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    calls = {}
    jours = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.afficher_message_insertion",
        lambda *a: calls.setdefault("afficher", True),
    )
    ctx = TimeSheetContext("log", [], {}, {})
    remplir_mission_specifique(None, "lundi", "8", jours, ctx)
    assert jours == ["lundi"]

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: calls.setdefault("effacer", True),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: True,
    )
    jours2 = []
    remplir_mission_specifique(None, "mardi", "8", jours2, ctx)
    assert "mardi" in jours2
    assert calls["effacer"]


def test_traiter_champs_mission(monkeypatch):
    ids = ["PROJECT_CODE$0", "SUB_CATEGORY_CODE$0", "ACTIVITY_CODE$0"]
    mapping = {
        "PROJECT_CODE$0": "project_code",
        "SUB_CATEGORY_CODE$0": "sub_category_code",
        "ACTIVITY_CODE$0": "activity_code",
    }
    info = {"project_code": "A"}
    log_calls = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: log_calls.append(msg),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    ctx = TimeSheetContext("log", [], {}, {})
    traiter_champs_mission(None, ids, mapping, info, ctx)
    assert any("PROJECT_CODE$0" in m for m in log_calls)
    assert any(messages.AUCUNE_VALEUR in m for m in log_calls)


def test_main_invokes_helper(monkeypatch):
    called = {}

    class DummyHelper:
        def __init__(self, ctx):
            called["init"] = ctx.log_file

        def run(self, driver):
            called["run"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.TimeSheetHelper", DummyHelper
    )

    main(None, "file")
    assert called == {"init": "file", "run": True}


def test_initialize_sets_globals(monkeypatch):
    fake = __import__("configparser").ConfigParser()
    fake["settings"] = {"liste_items_planning": '"d1", "d2"'}
    fake["work_schedule"] = {"lun": "En mission,8"}
    fake["project_information"] = {"billing_action": "Facturable"}
    fake["cgi_options_billing_action"] = {"Facturable": "B"}

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.read_config_ini",
        lambda lf: fake,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.set_log_file_selenium",
        lambda lf: None,
    )

    ctx = initialize("logfile")

    assert ["d1", "d2"] == ctx.liste_items_descriptions
    assert {"lun": ("En mission", "8")} == ctx.jours_de_travail
    assert {"billing_action": "B"} == ctx.informations_projet_mission


def test_traiter_champs_mission_insert(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "VAL"}
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    seq = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: seq.append("effacer"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: seq.append("insert") or True,
    )

    ctx = TimeSheetContext("log", [], {}, {})
    traiter_champs_mission(None, ids, mapping, info, ctx)
    assert seq == ["effacer", "insert"]


def test_main_with_mission(monkeypatch):
    seq = []

    class DummyHelper:
        def __init__(self, ctx):
            seq.append("init")

        def run(self, driver):
            seq.append("run")

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.TimeSheetHelper", DummyHelper
    )

    main(None, "file")
    assert seq == ["init", "run"]


def test_traiter_champs_mission_error(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "VAL"}
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )

    class DummyError(Exception):
        pass

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.StaleElementReferenceException()
        ),
    )

    ctx = TimeSheetContext("log", [], {}, {})
    traiter_champs_mission(None, ids, mapping, info, ctx, max_attempts=1)
    assert any(messages.REFERENCE_OBSOLETE in m for m in logs)


def test_main_handles_exception(monkeypatch):
    logs = []

    def raise_timeout(*_a, **_k):
        raise __import__("selenium").common.exceptions.TimeoutException()

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.TimeSheetHelper.fill_standard_days",
        raise_timeout,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.log_error",
        lambda msg, *_: logs.append(msg),
    )

    main(None, "file")
    assert any("Temps d'attente" in m for m in logs)
