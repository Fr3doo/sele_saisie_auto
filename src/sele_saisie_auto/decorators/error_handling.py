from __future__ import annotations

"""Decorator helpers for uniform Selenium error logging."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

from sele_saisie_auto import messages
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.selenium_utils import get_default_logger


def handle_selenium_errors(
    logger: Logger | None = None,
    default_return: Any | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator catching common Selenium exceptions.

    Parameters
    ----------
    logger:
        Optional :class:`Logger` to use for error reporting. If ``None``
        the default Selenium utils logger is used.
    default_return:
        Value returned when an exception is intercepted.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log = logger or get_default_logger()
            try:
                return func(*args, **kwargs)
            except NoSuchElementException as exc:
                log.error(f"❌ Élément {messages.INTROUVABLE} : {exc}")
            except TimeoutException as exc:
                log.error(f"❌ Temps d'attente dépassé : {exc}")
            except StaleElementReferenceException as exc:
                log.error(f"❌ {messages.REFERENCE_OBSOLETE} détectée : {exc}")
            except WebDriverException as exc:
                log.error(f"❌ Erreur {messages.WEBDRIVER} : {exc}")
            except Exception as exc:  # noqa: BLE001
                log.error(f"❌ {messages.ERREUR_INATTENDUE} : {exc}")
            return default_return

        return wrapper

    return decorator


__all__ = ["handle_selenium_errors"]
