import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    StaleElementReferenceException,
)

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto.decorators import handle_selenium_errors  # noqa: E402


def test_logs_no_such_element_and_returns_fallback(dummy_logger):
    @handle_selenium_errors(logger=dummy_logger, default_return="fallback")
    def failing():
        raise NoSuchElementException("missing")

    assert failing() == "fallback"
    assert any(messages.INTROUVABLE in msg for msg in dummy_logger.records["error"])


def test_logs_stale_reference_and_returns_fallback(dummy_logger):
    @handle_selenium_errors(logger=dummy_logger, default_return=42)
    def failing():
        raise StaleElementReferenceException("stale")

    assert failing() == 42
    assert any(
        messages.REFERENCE_OBSOLETE in msg for msg in dummy_logger.records["error"]
    )
