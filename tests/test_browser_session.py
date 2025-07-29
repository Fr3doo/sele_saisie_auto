import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.browser_session import BrowserSession  # noqa: E402
from sele_saisie_auto.exceptions import DriverError  # noqa: E402
from sele_saisie_auto.selenium_utils import Waiter  # noqa: E402


def test_open_delegates_to_manager(monkeypatch):
    calls = {}

    class DummyManager:
        def __init__(self, log_file: str) -> None:
            calls["init"] = log_file

        def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
            calls["args"] = (url, fullscreen, headless, no_sandbox)
            return "driver"

        def close(self):
            calls["closed"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )
    dummy_waiter = Waiter()
    monkeypatch.setattr(
        dummy_waiter, "wait_for_dom_ready", lambda d, t: calls.setdefault("ready", True)
    )
    session = BrowserSession("log.html", waiter=dummy_waiter)
    driver = session.open("http://t", fullscreen=True, headless=True)

    assert driver == "driver"  # nosec B101
    assert session.driver == "driver"  # nosec B101
    assert calls["args"] == ("http://t", True, True, False)  # nosec B101
    assert calls["init"] == "log.html"  # nosec B101


def test_close_calls_manager(monkeypatch):
    closed = {}

    class DummyManager:
        def __init__(self, log_file: str) -> None:
            pass

        def open(self, *a, **k):
            return "driver"

        def close(self):
            closed["called"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )
    session = BrowserSession("log.html")
    session.driver = "driver"
    session._manager = DummyManager("log.html")
    session.close()

    assert closed.get("called") is True  # nosec B101
    assert session.driver is None  # nosec B101


def test_context_manager(monkeypatch):
    closed = {}

    class DummyManager:
        def __init__(self, log_file: str) -> None:
            pass

        def open(self, *a, **k):
            return "driver"

        def close(self):
            closed["called"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )

    with BrowserSession("log.html") as session:
        assert isinstance(session, BrowserSession)  # nosec B101

    assert closed.get("called") is True  # nosec B101


def test_open_and_close_log(monkeypatch):
    logs = []

    class DummyManager:
        def __init__(self, log_file: str) -> None:
            pass

        def open(self, *a, **k):
            return "driver"

        def close(self):
            logs.append("closed")

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.write_log",
        lambda msg, lf, level: logs.append(msg),
    )
    dummy_waiter = Waiter()
    monkeypatch.setattr(
        dummy_waiter, "wait_for_dom_ready", lambda d, t: logs.append("ready")
    )
    session = BrowserSession("log.html", waiter=dummy_waiter)
    session.open("http://t")
    session.close()

    assert any("Ouverture du navigateur" in msg for msg in logs)
    assert any("Fermeture du navigateur" in msg for msg in logs)
    assert "closed" in logs


def test_open_failure_logs_and_raises(monkeypatch):
    records = []

    class DummyManager:
        def __init__(self, log_file: str) -> None:
            pass

        def open(self, *a, **k):
            raise Exception("boom")

        def close(self):
            pass

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.write_log",
        lambda msg, lf, level: records.append(msg),
    )
    session = BrowserSession("log.html")

    with pytest.raises(DriverError):
        session.open("http://t")

    assert any("boom" in msg for msg in records)


def test_wait_for_dom(monkeypatch):
    calls = []
    dummy = Waiter()
    monkeypatch.setattr(
        dummy,
        "wait_until_dom_is_stable",
        lambda d, timeout=10: (calls.append("stable") or True),
    )
    monkeypatch.setattr(
        dummy, "wait_for_dom_ready", lambda d, timeout: calls.append("ready")
    )
    session = BrowserSession("log.html", waiter=dummy)
    session.wait_for_dom("drv")

    assert calls == ["stable", "ready"]


def test_wait_for_dom_raises_after_attempts(monkeypatch):
    calls = {"stable": 0, "ready": 0}
    dummy = Waiter()
    monkeypatch.setattr(
        dummy,
        "wait_until_dom_is_stable",
        lambda d, timeout=10: (
            calls.__setitem__("stable", calls["stable"] + 1) or False
        ),
    )
    monkeypatch.setattr(
        dummy,
        "wait_for_dom_ready",
        lambda d, timeout: calls.__setitem__("ready", calls["ready"] + 1),
    )
    session = BrowserSession("log.html", waiter=dummy)
    with pytest.raises(RuntimeError):
        session.wait_for_dom("drv", max_attempts=2)
    assert calls["stable"] == 2
    assert calls["ready"] == 0


def test_go_to_iframe_and_default_content(monkeypatch):
    calls = []

    class DummySwitch:
        def frame(self, element):
            calls.append("frame")

        def default_content(self):
            calls.append("default")

    class DummyDriver:
        def __init__(self):
            self.switch_to = DummySwitch()

        def find_element(self, by, name):
            return "elem"

    session = BrowserSession("log.html")
    session.driver = DummyDriver()

    assert session.go_to_iframe("id") is True
    session.go_to_default_content()
    assert calls == ["frame", "default"]


def test_go_to_iframe_fail(monkeypatch):
    class DummySwitch:
        def frame(self, elem):
            raise Exception("boom")

        def default_content(self):
            pass

    class DummyDriver:
        def __init__(self):
            self.switch_to = DummySwitch()

        def find_element(self, by, name):
            raise Exception("nope")

    session = BrowserSession("log.html")
    session.driver = DummyDriver()

    assert session.go_to_iframe("id") is False
