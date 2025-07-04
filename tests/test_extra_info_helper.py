import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto import remplir_informations_supp_utils as risu  # noqa: E402
from sele_saisie_auto.additional_info_locators import (  # noqa: E402
    AdditionalInfoLocators,
)
from sele_saisie_auto.remplir_informations_supp_utils import (  # noqa: E402
    ExtraInfoHelper,
)


def make_config(**overrides):
    base_values = {day: f"val_{day}" for day in risu.JOURS_SEMAINE.values()}
    cfg = {
        "description_cible": "desc",
        "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
        "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
        "type_element": "input",
        "valeurs_a_remplir": base_values,
    }
    cfg.update(overrides)
    return cfg


def test_traiter_description_not_found(monkeypatch):
    messages = []
    monkeypatch.setattr(risu, "write_log", lambda msg, f, level: messages.append(msg))
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: None)
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, make_config())
    assert any("non trouv\u00e9e" in m for m in messages)


def test_traiter_description_input(monkeypatch):
    logs = []
    monkeypatch.setattr(risu, "write_log", lambda msg, f, level: logs.append(msg))
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: 2)

    class DummyElement:
        def __init__(self):
            self.value = ""

        def get_attribute(self, name):
            return self.value

        def clear(self):
            self.value = ""

        def send_keys(self, val):
            self.value = val

    def fake_wait(driver, by, ident, timeout):
        return DummyElement()

    monkeypatch.setattr(risu, "wait_for_element", fake_wait)
    monkeypatch.setattr(
        risu, "verifier_champ_jour_rempli", lambda el, jour: jour == "dimanche"
    )
    filled = []
    monkeypatch.setattr(
        risu, "remplir_champ_texte", lambda el, jour, val: filled.append((jour, val))
    )

    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, make_config())

    assert ("lundi", "val_lundi") in filled
    assert ("dimanche", "val_dimanche") not in filled
    assert any(messages.REMPLISSAGE in m for m in logs)


def test_traiter_description_select_special(monkeypatch):
    logs = []
    monkeypatch.setattr(risu, "write_log", lambda msg, f, level: logs.append(msg))
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: 0)
    ids = []

    def fake_wait(driver, by, ident, timeout):
        ids.append(ident)
        if ident.endswith("14$0"):
            return None
        return object()

    monkeypatch.setattr(risu, "wait_for_element", fake_wait)
    monkeypatch.setattr(risu, "verifier_champ_jour_rempli", lambda el, jour: False)
    selected = []
    monkeypatch.setattr(
        risu,
        "selectionner_option_menu_deroulant_type_select",
        lambda el, val: selected.append(val),
    )

    cfg = make_config(
        type_element="select",
        id_value_jours=AdditionalInfoLocators.DAY_UC_DAILYREST_SPECIAL.value,
    )
    del cfg["valeurs_a_remplir"]["mardi"]
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, cfg)

    assert f"{cfg['id_value_jours']}11$0" in ids
    assert selected
    assert any(messages.AUCUNE_VALEUR in m for m in logs)
    assert any(messages.IMPOSSIBLE_DE_TROUVER in m for m in logs)


def test_traiter_description_unknown_type(monkeypatch):
    monkeypatch.setattr(risu, "write_log", lambda *a, **k: None)
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: 1)
    monkeypatch.setattr(risu, "wait_for_element", lambda *a, **k: object())
    monkeypatch.setattr(risu, "verifier_champ_jour_rempli", lambda *a, **k: False)
    called = []
    monkeypatch.setattr(
        risu,
        "selectionner_option_menu_deroulant_type_select",
        lambda *a, **k: called.append("select"),
    )
    monkeypatch.setattr(
        risu, "remplir_champ_texte", lambda *a, **k: called.append("input")
    )
    cfg = make_config(type_element="other")
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, cfg)
    assert not called
