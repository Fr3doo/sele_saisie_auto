import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    afficher_message_insertion,
    main,
    remplir_jours,
    remplir_mission,
    remplir_mission_specifique,
    traiter_champs_mission,
    traiter_jour,
    wait_for_dom,
)

pytestmark = pytest.mark.slow


def test_wait_for_dom(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_until_dom_is_stable",
        lambda driver, timeout: calls.setdefault("stable", timeout),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom_ready",
        lambda driver, timeout: calls.setdefault("ready", timeout),
    )
    wait_for_dom(None)
    assert calls == {"stable": 10, "ready": 20}


def test_afficher_message_insertion_branch(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    afficher_message_insertion("lun", "8", 1, messages.TENTATIVE_INSERTION)
    assert f"{messages.TENTATIVE_INSERTION}2" in logs[0]


def test_remplir_jours(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.verifier_champ_jour_rempli",
        lambda *a, **k: "lundi",
    )
    result = remplir_jours(None, ["desc"], {2: "lundi"}, [])
    assert result == ["lundi"]


def test_traiter_jour_failure(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.StaleElementReferenceException()
        ),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.MAX_ATTEMPTS", 1
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    result = traiter_jour(None, "lundi", "desc", "8", [])
    assert result == []
    assert any(messages.ECHEC_INSERTION in m for m in logs)


def test_remplir_mission_dispatch(monkeypatch):
    called = {}

    def fake_traiter(driver, j, d, v, jr):
        called.setdefault("jour", True)
        return jr

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.traiter_jour",
        fake_traiter,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_mission_specifique",
        lambda *a, **k: called.setdefault("spec", True),
    )
    remplir_mission(
        None,
        {"lundi": ("desc", "8"), "mardi": ("En mission", "8")},
        [],
    )
    assert {"jour", "spec"} <= called.keys()

    # branch where conditions are false
    remplir_mission(None, {"mardi": ("desc", "8")}, ["mardi"])


def test_remplir_mission_specifique_failure(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.StaleElementReferenceException()
        ),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.MAX_ATTEMPTS", 1
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    remplir_mission_specifique(None, "mardi", "8", [])
    assert any(messages.ECHEC_INSERTION in m for m in logs)


def test_remplir_mission_specifique_insertion_fail(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.MAX_ATTEMPTS", 1
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    remplir_mission_specifique(None, "mercredi", "8", [])
    assert any(messages.ECHEC_INSERTION in m for m in logs)


def test_run_as_script(monkeypatch):
    called = {}
    fake_shared = types.ModuleType("sele_saisie_auto.shared_utils")
    fake_shared.get_log_file = lambda: "file"
    fake_shared.program_break_time = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "sele_saisie_auto.shared_utils", fake_shared)
    import importlib

    mod = importlib.import_module("sele_saisie_auto.remplir_jours_feuille_de_temps")
    monkeypatch.setattr(
        mod,
        "main",
        lambda driver, log: called.setdefault("main", (driver, log)),
    )

    prefix = "\n" * 469
    code = (
        prefix
        + "if __name__ == '__main__':\n    from sele_saisie_auto.shared_utils import get_log_file\n\n    main(None, get_log_file())\n"
    )
    exec(
        compile(code, mod.__file__, "exec"),
        {
            "__name__": "__main__",
            "main": mod.main,
            "get_log_file": fake_shared.get_log_file,
        },
    )
    assert called["main"] == (None, "file")


def test_remplir_jours_branches(monkeypatch):
    # row_index None branch
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: None,
    )
    result = remplir_jours(None, ["x"], {1: "dimanche"}, [])
    assert result == []

    # element None branch
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: None,
    )
    assert remplir_jours(None, ["x"], {1: "dimanche"}, []) == []


def test_traiter_jour_no_element(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: None,
    )
    assert traiter_jour(None, "lundi", "desc", "8", []) == []


def test_traiter_jour_controle_insertion_fail(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.trouver_ligne_par_description",
        lambda *a: 0,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.MAX_ATTEMPTS", 2
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    assert traiter_jour(None, "lundi", "desc", "8", []) == []
    assert any(messages.ECHEC_INSERTION in m for m in logs)


def test_remplir_mission_specifique_element_none(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: None,
    )
    assert remplir_mission_specifique(None, "lundi", "8", []) is None


def test_traiter_champs_mission_element_none(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "A"}
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda *a, **k: None,
    )
    traiter_champs_mission(None, ids, mapping, info)


def test_traiter_champs_mission_insertion_fail(monkeypatch):
    ids = ["PROJECT_CODE$0"]
    mapping = {"PROJECT_CODE$0": "project_code"}
    info = {"project_code": "VAL"}
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), False),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.effacer_et_entrer_valeur",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.program_break_time",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.MAX_ATTEMPTS", 1
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, *_: logs.append(msg),
    )
    traiter_champs_mission(None, ids, mapping, info, max_attempts=1)
    assert any(messages.ECHEC_INSERTION in m for m in logs)


def test_main_handles_other_exceptions(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.initialize", lambda lf: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.NoSuchElementException()
        ),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.log_error",
        lambda msg, *_: logs.append(msg),
    )
    main(None, "log")
    assert any(messages.INTROUVABLE in m for m in logs)


def test_main_webdriver_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.initialize", lambda lf: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.WebDriverException()
        ),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.log_error",
        lambda msg, *_: logs.append(msg),
    )
    main(None, "log")
    assert any(messages.WEBDRIVER in m for m in logs)


def test_main_stale_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.initialize", lambda lf: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: (_ for _ in ()).throw(
            __import__("selenium").common.exceptions.StaleElementReferenceException()
        ),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.log_error",
        lambda msg, *_: logs.append(msg),
    )
    main(None, "log")
    assert any(messages.REFERENCE_OBSOLETE in m for m in logs)


def test_main_generic_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.initialize", lambda lf: None
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.remplir_jours",
        lambda *a, **k: (_ for _ in ()).throw(Exception("boom")),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.log_error",
        lambda msg, *_: logs.append(msg),
    )
    main(None, "log")
    assert any(messages.ERREUR_INATTENDUE in m for m in logs)
