import sys
import types
from configparser import ConfigParser
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402
from tests.test_saisie_automatiser_psatime import (  # noqa: E402
    DummySHMService,
    setup_init,
)


class DummyManager:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def make_config():
    cfg = ConfigParser()
    cfg["credentials"] = {"login": "enc_login", "mdp": "enc_pwd"}
    cfg["settings"] = {
        "url": "http://test",
        "date_cible": "01/07/2024",
        "liste_items_planning": '"desc"',
    }
    cfg["work_schedule"] = {"lundi": "En mission,8"}
    cfg["project_information"] = {"billing_action": "Facturable"}
    cfg["additional_information_rest_period_respected"] = {"lundi": "Oui"}
    cfg["additional_information_work_time_range"] = {"lundi": "8-16"}
    cfg["additional_information_half_day_worked"] = {"lundi": "Non"}
    cfg["additional_information_lunch_break_duration"] = {"lundi": "1"}
    cfg["work_location_am"] = {"lundi": "CGI"}
    cfg["work_location_pm"] = {"lundi": "CGI"}
    cfg["cgi_options_billing_action"] = {"Facturable": "B"}
    return cfg


def test_wait_for_dom(monkeypatch):
    calls = []
    monkeypatch.setattr(
        sap,
        "wait_until_dom_is_stable",
        lambda driver, timeout=10: calls.append("stable"),
    )
    monkeypatch.setattr(
        sap, "wait_for_dom_ready", lambda driver, timeout: calls.append("ready")
    )
    sap.wait_for_dom("driver")
    assert calls == ["stable", "ready"]


def test_navigate_from_work_schedule_positive(monkeypatch):
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: True)
    actions = []
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: actions.append("click")
    )
    monkeypatch.setattr(
        sap, "switch_to_default_content", lambda *a, **k: actions.append("switch")
    )
    sap.navigate_from_work_schedule_to_additional_information_page("drv")
    assert actions.count("click") == 1
    assert "switch" in actions


def test_submit_and_validate_additional_information_positive(monkeypatch):
    seq = iter([True, True, True])
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: next(seq))
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: True)
    records = []
    monkeypatch.setattr(
        sap, "traiter_description", lambda *a, **k: records.append("desc")
    )
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: records.append("log"))
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: records.append("ok")
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap.context.descriptions = [
        {
            "description_cible": "d",
            "id_value_ligne": "x",
            "id_value_jours": "y",
            "type_element": "input",
            "valeurs_a_remplir": {"lundi": "1"},
        }
    ]
    sap.submit_and_validate_additional_information("drv")
    assert "desc" in records
    assert "ok" in records


def test_initialize_debug_mode_off(monkeypatch):
    cfg = make_config()
    from sele_saisie_auto.app_config import AppConfig

    app_cfg = AppConfig.from_parser(cfg)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    messages = []
    monkeypatch.setattr(sap, "write_log", lambda msg, f, level: messages.append(msg))
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "set_log_file_infos", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf, shm=None: DummyManager())
    app_cfg.debug_mode = "OFF"
    sap.initialize("log.html", app_cfg)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    assert not messages  # no debug logs when debug_mode is OFF


def test_switch_to_iframe_main_target_win0_no_element(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: False)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    with pytest.raises(NameError):
        sap.switch_to_iframe_main_target_win0("drv")


def test_navigate_from_home_to_date_entry_page_no_elements(monkeypatch):
    setup_init(monkeypatch)
    seq = iter([False, False])

    def fake_wait(*a, **k):
        try:
            return next(seq)
        except StopIteration:
            return False

    monkeypatch.setattr(sap, "wait_for_element", fake_wait)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "switch_to_iframe_main_target_win0",
        lambda self, *a, **k: True,
    )
    sap.navigate_from_home_to_date_entry_page("drv")


def test_handle_date_input_no_element(monkeypatch):
    setup_init(monkeypatch)
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: None)
    log = []
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: log.append("log"))
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: log.append("dom")
    )
    sap.handle_date_input("drv", "10/07/2024")
    assert "dom" in log


def test_submit_and_validate_additional_information_none(monkeypatch):
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: False)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    with pytest.raises(NameError):
        sap.submit_and_validate_additional_information("drv")


def test_cleanup_resources_none(monkeypatch):
    mgr = DummyManager()
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    sap.context.encryption_service = DummyManager()
    sap.context.shared_memory_service = DummySHMService()
    sap.cleanup_resources(mgr, None, None, None)
    assert mgr.closed is True
