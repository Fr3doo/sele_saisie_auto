import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from selenium_driver_manager import SeleniumDriverManager  # noqa: E402


def test_open_calls_utils(monkeypatch):
    calls = {}

    def fake_open(plein_ecran, url, headless, no_sandbox):
        calls["args"] = (plein_ecran, url, headless, no_sandbox)

        class Dummy:
            def quit(self):
                pass

        return Dummy()

    monkeypatch.setattr(
        "selenium_driver_manager.ouvrir_navigateur_sur_ecran_principal", fake_open
    )
    monkeypatch.setattr(
        "selenium_driver_manager.definir_taille_navigateur",
        lambda driver, w, h: driver,
    )
    monkeypatch.setattr("selenium_driver_manager.wait_for_dom_ready", lambda d, t: None)

    manager = SeleniumDriverManager("log.html")
    driver = manager.open("http://test", fullscreen=True, headless=True)

    assert driver is manager.driver  # nosec B101
    assert calls["args"] == (True, "http://test", True, False)  # nosec B101


def test_close_quits_driver(monkeypatch):
    closed = {}

    class Dummy:
        def quit(self):
            closed["quit"] = True

    manager = SeleniumDriverManager("log.html")
    manager.driver = Dummy()
    manager.close()

    assert closed.get("quit") is True  # nosec B101
    assert manager.driver is None  # nosec B101


def test_open_returns_none(monkeypatch):
    monkeypatch.setattr(
        "selenium_driver_manager.ouvrir_navigateur_sur_ecran_principal",
        lambda *a, **k: None,
    )
    manager = SeleniumDriverManager("log.html")
    assert manager.open("http://test") is None


def test_close_with_no_driver():
    manager = SeleniumDriverManager("log.html")
    manager.close()  # Should not raise
