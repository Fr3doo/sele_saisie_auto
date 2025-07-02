import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from remplir_jours_feuille_de_temps import (
    initialize,
    traiter_jour,
    remplir_mission_specifique,
    traiter_champs_mission,
    main,
)


def test_traiter_jour_paths(monkeypatch):
    # already filled
    assert traiter_jour(None, "lundi", "desc", "8", ["lundi"]) == ["lundi"]

    # row not found
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.trouver_ligne_par_description", lambda *a: None
    )
    result = traiter_jour(None, "lundi", "desc", "8", [])
    assert result == []

    # value already correct
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.trouver_ligne_par_description", lambda *a: 0
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_element", lambda *a, **k: object()
    )
    calls = {}
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.afficher_message_insertion",
        lambda *a: calls.setdefault("afficher", []).append(a),
    )
    result = traiter_jour(None, "lundi", "desc", "8", [])
    assert result == ["lundi"]
    assert calls["afficher"]

    # need insertion
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: calls.setdefault("effacer", True),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.controle_insertion", lambda *a, **k: True
    )
    result = traiter_jour(None, "mardi", "desc", "8", [])
    assert "mardi" in result
    assert calls["effacer"]


def test_remplir_mission_specifique(monkeypatch):
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_element", lambda *a, **k: object()
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    calls = {}
    jours = []
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.afficher_message_insertion",
        lambda *a: calls.setdefault("afficher", True),
    )
    remplir_mission_specifique(None, "lundi", "8", jours)
    assert jours == ["lundi"]

    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: calls.setdefault("effacer", True),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.program_break_time", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.controle_insertion", lambda *a, **k: True
    )
    jours2 = []
    remplir_mission_specifique(None, "mardi", "8", jours2)
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
        "remplir_jours_feuille_de_temps.write_log", lambda msg, *_: log_calls.append(msg)
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_element", lambda *a, **k: object()
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    traiter_champs_mission(None, ids, mapping, info)
    assert any("PROJECT_CODE$0" in m for m in log_calls)
    assert any("Aucune valeur" in m for m in log_calls)


def test_main_invokes_helpers(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.initialize", lambda lf: called.setdefault("init", True)
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: called.setdefault("jours", True) or [],
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.remplir_mission",
        lambda *a, **k: called.setdefault("mission", True) or [],
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.est_en_mission_presente", lambda *_: False
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.write_log", lambda *a, **k: called.setdefault("log", 0)
    )
    main(None, "file")
    assert {"init", "jours", "mission", "log"} <= called.keys()


def test_initialize_sets_globals(monkeypatch):
    fake = __import__("configparser").ConfigParser()
    fake["settings"] = {"liste_items_planning": '"d1", "d2"'}
    fake["work_schedule"] = {"lun": "En mission,8"}
    fake["project_information"] = {"billing_action": "Facturable"}

    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.read_config_ini", lambda lf: fake
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.set_log_file_selenium", lambda lf: None
    )

    initialize("logfile")

    assert ["d1", "d2"] == \
        __import__("remplir_jours_feuille_de_temps").LISTE_ITEMS_DESCRIPTIONS
    assert {"lun": ("En mission", "8")} == \
        __import__("remplir_jours_feuille_de_temps").JOURS_DE_TRAVAIL
    assert {"billing_action": "B"} == \
        __import__("remplir_jours_feuille_de_temps").INFORMATIONS_PROJET_MISSION


def test_traiter_champs_mission_insert(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "VAL"}
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.write_log", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_element", lambda *a, **k: object()
    )
    seq = []
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: seq.append("effacer"),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.program_break_time", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: seq.append("insert") or True,
    )

    traiter_champs_mission(None, ids, mapping, info)
    assert seq == ["effacer", "insert"]


def test_main_with_mission(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.initialize", lambda lf: called.setdefault("init", True)
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: called.setdefault("jours", True) or [],
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.remplir_mission",
        lambda *a, **k: called.setdefault("mission", True) or [],
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.est_en_mission_presente", lambda *_: True
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.traiter_champs_mission", lambda *a, **k: called.setdefault("traite", True)
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.write_log", lambda *a, **k: called.setdefault("log", 0)
    )

    main(None, "file")
    assert {"init", "jours", "mission", "traite", "log"} <= called.keys()


def test_traiter_champs_mission_error(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "VAL"}
    logs = []
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.write_log", lambda msg, *_: logs.append(msg)
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_dom", lambda *_: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.wait_for_element", lambda *a, **k: object()
    )

    class DummyEx(Exception):
        pass

    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (_ for _ in ()).throw(__import__('selenium').common.exceptions.StaleElementReferenceException()),
    )

    traiter_champs_mission(None, ids, mapping, info, max_attempts=1)
    assert any("Référence obsolète" in m for m in logs)


def test_main_handles_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.initialize", lambda lf: None
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: (_ for _ in ()).throw(__import__('selenium').common.exceptions.TimeoutException()),
    )
    monkeypatch.setattr(
        "remplir_jours_feuille_de_temps.write_log", lambda msg, *_: logs.append(msg)
    )

    main(None, "file")
    assert any("Temps d'attente" in m for m in logs)
