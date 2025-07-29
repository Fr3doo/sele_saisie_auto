import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.additional_info_page import (  # noqa: E402
    AdditionalInfoPage,
)
from sele_saisie_auto.logging_service import Logger  # noqa: E402


class DummyAutomation:
    def __init__(self):
        self.log_file = "log.html"
        self.logger = Logger(self.log_file)
        self.context = types.SimpleNamespace(
            descriptions=[
                {
                    "description_cible": "d",
                    "id_value_ligne": "x",
                    "id_value_jours": "y",
                    "type_element": "select",
                    "valeurs_a_remplir": {"lundi": "1"},
                }
            ]
        )
        self.browser_session = types.SimpleNamespace(
            go_to_iframe=lambda *a, **k: True,
            go_to_default_content=lambda *a, **k: None,
        )

    def wait_for_dom(self, driver, max_attempts: int = 3):
        pass


def test_navigate_from_work_schedule(monkeypatch):
    dummy = DummyAutomation()
    page = AdditionalInfoPage(dummy)
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: True)
    clicks = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: clicks.append(True),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.BrowserSession.go_to_default_content",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(AdditionalInfoPage, "wait_for_dom", lambda self, d: None)
    page.navigate_from_work_schedule_to_additional_information_page("drv")
    assert clicks


def test_submit_and_validate_additional_information(monkeypatch):
    dummy = DummyAutomation()
    page = AdditionalInfoPage(dummy)
    seq = iter([True, True])
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: next(seq))
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.BrowserSession.go_to_iframe",
        lambda *a, **k: True,
    )
    records = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.traiter_description",
        lambda *a, **k: records.append("desc"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.logger_utils.write_log",
        lambda msg, f, level: records.append("log"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: records.append("ok"),
    )
    monkeypatch.setattr(AdditionalInfoPage, "wait_for_dom", lambda self, d: None)
    page.submit_and_validate_additional_information("drv")
    assert "desc" in records
    assert "ok" in records


def test_save_draft_and_validate(monkeypatch):
    dummy = DummyAutomation()
    page = AdditionalInfoPage(dummy)
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: True)
    clicks = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: clicks.append(True),
    )
    monkeypatch.setattr(AdditionalInfoPage, "wait_for_dom", lambda self, d: None)
    calls = []
    monkeypatch.setattr(
        page.alert_handler,
        "handle_alerts",
        lambda d, alert_type="save_alerts": calls.append((d, alert_type)),
    )
    assert page.save_draft_and_validate("drv") is True
    assert clicks
    assert ("drv", "save_alerts") in calls


def test_handle_save_alerts(monkeypatch):
    dummy = DummyAutomation()
    page = AdditionalInfoPage(dummy)
    calls = []

    def fake_handle(driver, alert_type="save_alerts"):
        calls.append((driver, alert_type))

    monkeypatch.setattr(page.alert_handler, "handle_alerts", fake_handle)
    page._handle_save_alerts("drv")
    assert ("drv", "save_alerts") in calls
