import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    afficher_message_insertion,
    ajouter_jour_a_jours_remplis,
    est_en_mission_presente,
    insert_with_retries,
)
from sele_saisie_auto.utils.misc import clear_screen  # noqa: E402
from sele_saisie_auto.utils.mission import est_en_mission  # noqa: E402


def test_utilities(monkeypatch):
    assert est_en_mission("En mission") is True
    assert est_en_mission("Autre") is False

    jours = {"lun": ("En mission", "8")}
    assert est_en_mission_presente(jours) is True

    filled_days = []
    assert ajouter_jour_a_jours_remplis("lun", filled_days) == ["lun"]
    assert ajouter_jour_a_jours_remplis("lun", filled_days) == ["lun"]

    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.write_log",
        lambda msg, file, level: logs.append(msg),
    )
    afficher_message_insertion("lun", "8", 0, "test")
    assert logs

    called = {}
    monkeypatch.setattr(
        "sele_saisie_auto.utils.misc.subprocess.run",
        lambda cmd, *a, **k: called.setdefault("cmd", cmd),
    )
    clear_screen()
    assert called["cmd"] in {"cls", "clear"}


def test_insert_with_retries(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )

    assert insert_with_retries(None, "ID", "8", None) is True


def test_insert_with_retries_fail(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
    )
    assert insert_with_retries(None, "ID", "8", None) is False


def test_insert_with_retries_insert(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_element",
        lambda *a, **k: object(),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
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
        lambda *a, **k: True,
    )
    assert insert_with_retries(None, "ID", "8", None) is True


def test_insert_with_retries_stale(monkeypatch):
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
    assert insert_with_retries(None, "ID", "8", None) is False
    assert logs


def test_insert_with_retries_waiter(monkeypatch):
    dummy = types.SimpleNamespace(
        wait_for_element=lambda *a, **k: object(),
        wait_until_dom_is_stable=lambda *a, **k: None,
        wait_for_dom_ready=lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.wait_for_dom",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.detecter_et_verifier_contenu",
        lambda *a, **k: (object(), True),
    )
    assert insert_with_retries(None, "ID", "8", dummy) is True
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
    assert insert_with_retries(None, "ID", "8", dummy) is False

    monkeypatch.setattr(
        "sele_saisie_auto.remplir_jours_feuille_de_temps.controle_insertion",
        lambda *a, **k: True,
    )
    assert insert_with_retries(None, "ID", "8", dummy) is True
