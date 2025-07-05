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

# Helper to build config dictionaries


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


def test_traiter_description_row_not_found(monkeypatch):
    logs = []
    monkeypatch.setattr(risu, "write_log", lambda msg, f, level: logs.append(msg))
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: None)
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, make_config())
    assert any("non trouv" in m for m in logs)


class DummyElement:
    def __init__(self):
        self.value = ""

    def get_attribute(self, name):
        return self.value

    def clear(self):
        self.value = ""

    def send_keys(self, val):
        self.value = val


def test_traiter_description_fill_input(monkeypatch):
    logs = []
    monkeypatch.setattr(risu, "write_log", lambda msg, f, level: logs.append(msg))
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: 1)

    ids = []

    def fake_wait(driver, by, ident, timeout):
        ids.append(ident)
        if ident.endswith("2$1"):
            return None  # simulate missing Monday field
        return DummyElement()

    monkeypatch.setattr(risu, "wait_for_element", fake_wait)
    monkeypatch.setattr(risu, "verifier_champ_jour_rempli", lambda el, jour: False)
    filled = []
    monkeypatch.setattr(
        risu, "remplir_champ_texte", lambda el, jour, val: filled.append((jour, val))
    )

    cfg = make_config()
    del cfg["valeurs_a_remplir"]["mardi"]
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, cfg)

    assert f"{AdditionalInfoLocators.DAY_UC_DAILYREST.value}1$1" in ids

    assert ("lundi", "val_lundi") not in filled  # element missing
    assert ("mardi", "val_mardi") not in filled  # value missing
    assert ("mercredi", "val_mercredi") in filled
    assert any(messages.AUCUNE_VALEUR in m for m in logs)
    assert any(messages.IMPOSSIBLE_DE_TROUVER in m for m in logs)


def test_traiter_description_select(monkeypatch):
    monkeypatch.setattr(risu, "trouver_ligne_par_description", lambda *a, **k: 2)
    monkeypatch.setattr(risu, "verifier_champ_jour_rempli", lambda *a, **k: False)
    monkeypatch.setattr(risu, "wait_for_element", lambda *a, **k: DummyElement())
    selected = []
    monkeypatch.setattr(
        risu,
        "selectionner_option_menu_deroulant_type_select",
        lambda el, val: selected.append(val),
    )

    cfg = make_config(type_element="select")
    helper = ExtraInfoHelper(log_file="log")
    helper.waiter = None
    helper.traiter_description(None, cfg)
    assert "val_lundi" in selected
