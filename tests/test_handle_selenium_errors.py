import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

from sele_saisie_auto.decorators import handle_selenium_errors  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402


def test_decorator_returns_default_on_error(monkeypatch):
    logs: list[str] = []

    class DummyLogger(Logger):
        def __init__(self) -> None:
            super().__init__("log")

        def error(self, message: str) -> None:  # type: ignore[override]
            logs.append(message)

    logger = DummyLogger()

    @handle_selenium_errors(logger=logger, default_return="fallback")
    def buggy():
        raise NoSuchElementException("boom")

    assert buggy() == "fallback"
    assert any("introuvable" in m for m in logs)


def test_decorator_passes_through(monkeypatch):
    @handle_selenium_errors(default_return="fallback")
    def ok():
        return 42

    assert ok() == 42


def test_decorator_handles_other_exceptions(monkeypatch):
    calls = []

    class DummyLogger(Logger):
        def __init__(self) -> None:
            super().__init__("log")

        def error(self, message: str) -> None:  # type: ignore[override]
            calls.append(message)

    logger = DummyLogger()

    @handle_selenium_errors(logger=logger, default_return=False)
    def raise_timeout():
        raise TimeoutException("too long")

    @handle_selenium_errors(logger=logger, default_return=False)
    def raise_stale():
        raise StaleElementReferenceException("stale")

    @handle_selenium_errors(logger=logger, default_return=False)
    def raise_driver():
        raise WebDriverException("driver")

    assert raise_timeout() is False
    assert raise_stale() is False
    assert raise_driver() is False
    assert len(calls) == 3


def test_decorator_uses_instance_logger(monkeypatch):
    records: list[str] = []

    class DummyLogger(Logger):
        def __init__(self) -> None:
            super().__init__("log")

        def error(self, message: str) -> None:  # type: ignore[override]
            records.append(message)

    class Dummy:
        def __init__(self) -> None:
            self.logger = DummyLogger()

        @handle_selenium_errors(default_return="fallback")
        def buggy(self):
            raise NoSuchElementException("oops")

    d = Dummy()
    assert d.buggy() == "fallback"
    assert any("introuvable" in m for m in records)
