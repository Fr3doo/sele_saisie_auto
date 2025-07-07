import types

import pytest

from sele_saisie_auto.alerts.alert_handler import AlertHandler


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


def test_handle_alerts_save(monkeypatch):
    dummy = DummyAutomation()
    handler = AlertHandler(dummy)
    seq = iter([True, False, False])
    monkeypatch.setattr(handler.waiter, "wait_for_element", lambda *a, **k: next(seq))
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: logs.append("click"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.write_log",
        lambda msg, f, level: logs.append(msg),
    )
    handler.handle_alerts("drv")
    assert "click" in logs


def test_handle_alerts_date(monkeypatch):
    dummy = DummyAutomation()
    handler = AlertHandler(dummy)
    monkeypatch.setattr(handler.waiter, "wait_for_element", lambda *a, **k: True)
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.click_element_without_wait",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.write_log",
        lambda *a, **k: None,
    )
    with pytest.raises(SystemExit):
        handler.handle_alerts("drv", alert_type="date_alert")


def test_handle_alerts_unknown(monkeypatch):
    handler = AlertHandler(DummyAutomation())
    with pytest.raises(ValueError):
        handler.handle_alerts("drv", alert_type="unknown")
