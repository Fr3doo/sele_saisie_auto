from types import SimpleNamespace

import pytest
from selenium.common.exceptions import TimeoutException

from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import wait_helpers as wh


def test_wait_for_element_no_locator(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, level="INFO", **k: logs.append(level))
    driver = SimpleNamespace(find_elements=lambda by, val: [])
    result = wh.Waiter(logger=logger).wait_for_element(driver, locator_value=None)
    assert result is None
    assert "ERROR" in logs


def test_wait_for_element_warning_on_timeout(monkeypatch):
    logs = []
    logger = Logger(None, writer=lambda msg, *a, level="INFO", **k: logs.append(level))

    class DummyWait:
        def __init__(self, driver, timeout):
            pass

        def until(self, cond):
            raise TimeoutException("timeout")

    monkeypatch.setattr(wh._wrapper, "WebDriverWait", DummyWait)
    driver = SimpleNamespace(find_elements=lambda by, val: [object()])

    with pytest.raises(TimeoutException):
        wh.Waiter(logger=logger).wait_for_element(driver, locator_value="x")

    assert "WARNING" in logs
