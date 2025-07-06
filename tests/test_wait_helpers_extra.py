from types import SimpleNamespace

from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import wait_helpers as wh


def test_wait_for_element_no_locator(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, level="INFO", **k: logs.append(level))
    driver = SimpleNamespace(find_elements=lambda by, val: [])
    result = wh.Waiter(logger=logger).wait_for_element(driver, locator_value=None)
    assert result is None
    assert "ERROR" in logs
