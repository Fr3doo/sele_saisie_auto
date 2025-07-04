from types import SimpleNamespace

from sele_saisie_auto.selenium_utils import wait_helpers as wh


def test_wait_for_element_no_locator(monkeypatch):
    logs = []
    monkeypatch.setattr(wh, "write_log", lambda msg, f, level: logs.append(level))
    driver = SimpleNamespace(find_elements=lambda by, val: [])
    result = wh.Waiter().wait_for_element(driver, locator_value=None)
    assert result is None
    assert "ERROR" in logs
