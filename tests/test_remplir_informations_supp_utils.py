# flake8: noqa
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import sele_saisie_auto.remplir_informations_supp_utils as risu  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.remplir_informations_supp_utils import (  # noqa: E402
    ExtraInfoHelper,
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


def test_pass_waiter_and_log(monkeypatch):
    captured = {}

    def fake_process(
        driver, config, log_file, waiter=None, *, filling_context=None, logger=None
    ):
        captured["waiter"] = waiter
        captured["log"] = log_file
        captured["config"] = config

    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log.html"))
    custom_waiter = object()
    helper.waiter = custom_waiter
    cfg = make_config()
    helper.traiter_description(None, cfg)
    assert captured["waiter"] is custom_waiter
    assert captured["log"] == helper.log_file
    assert captured["config"] is cfg


def test_unknown_type_context_none(monkeypatch):
    captured = {}

    def fake_process(
        driver, config, log_file, waiter=None, *, filling_context=None, logger=None
    ):
        captured["context"] = filling_context

    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log"))
    helper.traiter_description(None, make_config(type_element="other"))
    assert captured["context"] is None
