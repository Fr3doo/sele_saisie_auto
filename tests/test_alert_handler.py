import types

import pytest
from selenium.webdriver.common.by import By

from sele_saisie_auto.alerts.alert_handler import AlertHandler
from sele_saisie_auto.enums import AlertType
from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.locators import Locators


class DummyAutomation:
    def __init__(self):
        self.log_file = "log.html"
        self.browser_session = types.SimpleNamespace(
            go_to_default_content=lambda *a, **k: None
        )
        self.context = types.SimpleNamespace(
            config=types.SimpleNamespace(default_timeout=1, long_timeout=1)
        )

    def wait_for_dom(self, driver):
        pass


def test_handle_alerts_clicks_confirm_ok_and_logs(monkeypatch):
    dummy = DummyAutomation()
    handler = AlertHandler(dummy)
    seq = iter([True, False, False])
    monkeypatch.setattr(handler.waiter, "wait_for_element", lambda *a, **k: next(seq))

    clicks = []

    def fake_click(driver, by, locator):
        clicks.append((by, locator))

    monkeypatch.setattr(
        "sele_saisie_auto.alerts.alert_handler.click_element_without_wait",
        fake_click,
    )

    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.alerts.alert_handler.write_log",
        lambda msg, f, level: logs.append((msg, level)),
    )

    handler.handle_alerts("drv")

    assert (By.ID, Locators.CONFIRM_OK.value) in clicks
    assert logs


def test_handle_alerts_date(monkeypatch):
    dummy = DummyAutomation()
    handler = AlertHandler(dummy)
    monkeypatch.setattr(handler.waiter, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(
        "sele_saisie_auto.alerts.alert_handler.click_element_without_wait",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.alerts.alert_handler.write_log",
        lambda *a, **k: None,
    )
    with pytest.raises(AutomationExitError):
        handler.handle_alerts("drv", alert_type=AlertType.DATE_ALERT)


def test_handle_alerts_unknown(monkeypatch):
    handler = AlertHandler(DummyAutomation())
    with pytest.raises(ValueError):
        handler.handle_alerts("drv", alert_type="unknown")
