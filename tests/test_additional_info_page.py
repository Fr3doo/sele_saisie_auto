import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.additional_info_page import (  # noqa: E402
    AdditionalInfoPage,
)


class DummyAutomation:
    def __init__(self):
        self.log_file = "log.html"
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

    def wait_for_dom(self, driver):
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
        "sele_saisie_auto.saisie_automatiser_psatime.switch_to_default_content",
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
        "sele_saisie_auto.saisie_automatiser_psatime.switch_to_iframe_by_id_or_name",
        lambda *a, **k: True,
    )
    records = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.traiter_description",
        lambda *a, **k: records.append("desc"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.write_log",
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
    assert page.save_draft_and_validate("drv") is True
    assert clicks


def test_handle_save_alerts(monkeypatch):
    dummy = DummyAutomation()
    page = AdditionalInfoPage(dummy)
    seq = iter([True, False, False])
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: next(seq))
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: logs.append("click"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.write_log",
        lambda msg, f, level: logs.append(msg),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.switch_to_default_content",
        lambda *a, **k: None,
    )
    page._handle_save_alerts("drv")
    assert "click" in logs
