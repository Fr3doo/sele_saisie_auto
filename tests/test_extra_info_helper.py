# flake8: noqa
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import types  # noqa: E402

import pytest  # noqa: E402

import sele_saisie_auto.remplir_informations_supp_utils as risu  # noqa: E402
from sele_saisie_auto.form_processing import description_processor as dp  # noqa: E402
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

    monkeypatch.setattr(dp, "process_description", fake_process)
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

    monkeypatch.setattr(dp, "process_description", fake_process)
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

    monkeypatch.setattr(dp, "process_description", fake_process)
    monkeypatch.setattr(risu, "process_description", fake_process)
    helper = ExtraInfoHelper(Logger("log"))
    helper.traiter_description(None, make_config(type_element="other"))
    assert captured["context"] is None


class DummyPage:
    def __init__(self):
        self.calls = []

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append(("nav", driver))
        return "nav"

    def submit_and_validate_additional_information(self, driver):
        self.calls.append(("submit", driver))
        return "submit"


class DummyTimeSheet:
    pass


def test_set_page_updates_helper(monkeypatch):
    helper = ExtraInfoHelper(Logger("log"))
    page = DummyPage()
    helper.set_page(page)
    assert helper.page is page


def test_set_timesheet_helper(monkeypatch):
    helper = ExtraInfoHelper(Logger("log"))
    ts = DummyTimeSheet()
    helper.set_timesheet_helper(ts)
    assert helper.timesheet_helper is ts


def test_navigation_delegates(monkeypatch):
    page = DummyPage()
    helper = ExtraInfoHelper(Logger("log"), page=page)
    result = helper.navigate_from_work_schedule_to_additional_information_page("drv")
    assert result == "nav"
    assert ("nav", "drv") in page.calls


def test_navigation_without_page(monkeypatch):
    helper = ExtraInfoHelper(Logger("log"))
    with pytest.raises(RuntimeError):
        helper.navigate_from_work_schedule_to_additional_information_page("drv")


def test_submit_delegates(monkeypatch):
    page = DummyPage()
    helper = ExtraInfoHelper(Logger("log"), page=page)
    result = helper.submit_and_validate_additional_information("drv")
    assert result == "submit"
    assert ("submit", "drv") in page.calls


def test_submit_without_page(monkeypatch):
    helper = ExtraInfoHelper(Logger("log"))
    with pytest.raises(RuntimeError):
        helper.submit_and_validate_additional_information("drv")


def test_constructor_injects_timesheet_helper(monkeypatch):
    ts = DummyTimeSheet()
    helper = ExtraInfoHelper(Logger("log"), timesheet_helper=ts)
    assert helper.timesheet_helper is ts


def test_waiter_created_with_factory(monkeypatch):
    captured = {}

    class DummyWaiter:
        def __init__(self):
            self.wrapper = types.SimpleNamespace()

    def fake_create_waiter(timeout):
        captured["timeout"] = timeout
        return DummyWaiter()

    monkeypatch.setattr(risu, "create_waiter", fake_create_waiter)
    helper = ExtraInfoHelper(
        Logger("log"),
        app_config=types.SimpleNamespace(default_timeout=3, long_timeout=6),
    )
    assert isinstance(helper.waiter, DummyWaiter)
    assert captured["timeout"] == 3
