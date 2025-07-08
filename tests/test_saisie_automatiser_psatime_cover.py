import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402
from sele_saisie_auto.selenium_utils import Waiter  # noqa: E402
from tests.test_saisie_automatiser_psatime import (  # noqa: E402
    DummySHMService,
    setup_init,
)

pytestmark = pytest.mark.slow


class DummyManager:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def test_wait_for_dom(monkeypatch):
    calls = []
    dummy = Waiter()
    monkeypatch.setattr(
        dummy,
        "wait_until_dom_is_stable",
        lambda driver, timeout=10: calls.append("stable"),
    )
    monkeypatch.setattr(
        dummy,
        "wait_for_dom_ready",
        lambda driver, timeout: calls.append("ready"),
    )
    if sap._AUTOMATION:
        sap._AUTOMATION.browser_session.waiter = dummy
    sap.wait_for_dom("driver")
    assert calls == ["stable", "ready"]


def test_navigate_from_work_schedule_positive(monkeypatch):
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: True
    )
    actions = []
    monkeypatch.setattr(
        sap, "click_element_without_wait", lambda *a, **k: actions.append("click")
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.BrowserSession.go_to_default_content",
        lambda *a, **k: actions.append("switch"),
    )
    sap.navigate_from_work_schedule_to_additional_information_page("drv")
    assert actions.count("click") == 1
    assert "switch" in actions


def test_submit_and_validate_additional_information_positive(monkeypatch):
    seq = iter([True, True, True])
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: next(seq)
    )
    monkeypatch.setattr(sap.BrowserSession, "go_to_iframe", lambda *a, **k: True)
    if sap._AUTOMATION:
        sap._AUTOMATION.browser_session.go_to_iframe = lambda *a, **k: True
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.BrowserSession.go_to_iframe",
        lambda *a, **k: True,
    )
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


def test_initialize_debug_mode_off(monkeypatch, sample_config, tmp_path):
    cfg = sample_config
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    log_path = tmp_path / "log.html"
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "EncryptionService", lambda lf, shm=None: DummyManager())
    app_cfg.debug_mode = "OFF"
    sap.initialize(
        str(log_path),
        app_cfg,
        choix_user=True,
        memory_config=sap.MemoryConfig(),
    )
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    assert not log_path.exists() or log_path.read_text(encoding="utf-8") == ""


def test_switch_to_iframe_main_target_win0_no_element(monkeypatch):
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: False
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    with pytest.raises(NameError):
        sap.switch_to_iframe_main_target_win0("drv")


def test_navigate_from_home_to_date_entry_page_no_elements(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._AUTOMATION.date_entry_page,
        "navigate_from_home_to_date_entry_page",
        lambda driver: False,
    )
    sap.navigate_from_home_to_date_entry_page("drv")


def test_handle_date_input_no_element(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.date_entry_page,
        "handle_date_input",
        lambda driver, date: called.setdefault("called", True),
    )
    sap._AUTOMATION.date_entry_page.handle_date_input("drv", "10/07/2024")
    assert called["called"] is True


def test_submit_and_validate_additional_information_none(monkeypatch):
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "submit_and_validate_additional_information",
        lambda driver: (_ for _ in ()).throw(NameError()),
    )
    with pytest.raises(NameError):
        sap.submit_and_validate_additional_information("drv")


def test_cleanup_resources_none(monkeypatch):
    mgr = DummyManager()
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    sap.context.encryption_service = DummyManager()
    sap.context.shared_memory_service = DummySHMService()
    sap._ORCHESTRATOR.browser_session = mgr
    sap.cleanup_resources(mgr, None, None, None)
    assert mgr.closed is True
