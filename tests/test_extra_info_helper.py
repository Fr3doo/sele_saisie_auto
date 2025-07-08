# flake8: noqa
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import sele_saisie_auto.remplir_informations_supp_utils as risu  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.remplir_informations_supp_utils import (  # noqa: E402
    ExtraInfoHelper,
)
from sele_saisie_auto.strategies.element_filling_strategy import (
    InputFillingStrategy,
    SelectFillingStrategy,
)


def make_config(**overrides):
    cfg = {
        "description_cible": "desc",
        "id_value_ligne": "row",
        "id_value_jours": "days",
        "type_element": "input",
        "valeurs_a_remplir": {},
    }
    cfg.update(overrides)
    return cfg


def test_delegate_strategy_input(monkeypatch):
    captured = {}

    def fake_process(
        driver, config, log_file, waiter=None, *, filling_context=None, logger=None
    ):
        captured["strategy"] = (
            filling_context.strategy.__class__ if filling_context else None
        )
        captured["logger"] = logger

    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log"))
    helper.traiter_description(None, make_config(type_element="input"))
    assert captured["strategy"] is InputFillingStrategy
    assert captured["logger"] is helper.logger


def test_delegate_strategy_select(monkeypatch):
    captured = {}

    def fake_process(
        driver, config, log_file, waiter=None, *, filling_context=None, logger=None
    ):
        captured["strategy"] = (
            filling_context.strategy.__class__ if filling_context else None
        )

    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log"))
    helper.traiter_description(None, make_config(type_element="select"))
    assert captured["strategy"] is SelectFillingStrategy


def test_delegate_strategy_unknown(monkeypatch):
    captured = {}

    def fake_process(
        driver, config, log_file, waiter=None, *, filling_context=None, logger=None
    ):
        captured["context"] = filling_context

    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log"))
    helper.traiter_description(None, make_config(type_element="other"))
    assert captured["context"] is None
