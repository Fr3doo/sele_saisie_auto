import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.browser_session import BrowserSession  # noqa: E402
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


def test_wait_for_dom(monkeypatch):
    calls = []
    dummy = Waiter()
    monkeypatch.setattr(
        dummy, "wait_until_dom_is_stable", lambda d, timeout=10: calls.append("stable")
    )
    monkeypatch.setattr(
        dummy, "wait_for_dom_ready", lambda d, timeout: calls.append("ready")
    )
    session = BrowserSession("log.html", waiter=dummy)
    session.wait_for_dom("drv")

    assert calls == ["stable", "ready"]
