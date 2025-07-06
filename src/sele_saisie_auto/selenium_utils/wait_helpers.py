"""Selenium wait helper functions."""

from __future__ import annotations

import time
from functools import wraps

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

from . import wrapper as _wrapper
from . import write_log

Wrapper = _wrapper.Wrapper
is_document_complete = _wrapper.is_document_complete
# ensure wrapper shares the same time module for monkeypatching in tests
_wrapper.time = time


class Waiter:
    """Utility object encapsulating explicit wait helpers."""

    def __init__(
        self,
        default_timeout: int = DEFAULT_TIMEOUT,
        long_timeout: int = LONG_TIMEOUT,
        wrapper: Wrapper | None = None,
    ) -> None:  # pragma: no cover - simple initializer
        """Configure les délais d'attente par défaut."""
        self.wrapper = wrapper or Wrapper(
            default_timeout,
            long_timeout,
            writer=write_log,
        )

    def wait_for_dom_ready(self, driver, timeout: int | None = None):
        """Wait until the DOM is fully loaded."""
        self.wrapper.wait_for_dom_ready(driver, timeout)

    def wait_until_dom_is_stable(self, driver, timeout: int | None = None) -> bool:
        """Return True when the DOM remains unchanged for ``timeout`` seconds."""
        return self.wrapper.wait_until_dom_is_stable(driver, timeout)

    def wait_for_element(
        self,
        driver,
        by=By.ID,
        locator_value=None,
        condition=ec.presence_of_element_located,
        timeout: int | None = None,
    ):
        """Wait for an element to satisfy ``condition`` or return ``None``."""
        return self.wrapper.wait_for_element(
            driver,
            by,
            locator_value,
            condition,
            timeout,
        )

    # Convenience wrappers -------------------------------------------------
    def find_clickable(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it becomes clickable."""
        return self.wrapper.find_clickable(driver, by, locator_value, timeout)

    def find_visible(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it is visible."""
        return self.wrapper.find_visible(driver, by, locator_value, timeout)

    def find_present(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it is present in the DOM."""
        return self.wrapper.find_present(driver, by, locator_value, timeout)


DEFAULT_WAITER = Waiter()


def wait_for_dom_ready(
    driver, timeout: int | None = None, waiter: Waiter | None = None
):
    """Wait until the DOM is fully loaded."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    w.wait_for_dom_ready(driver, timeout)


def wait_until_dom_is_stable(
    driver, timeout: int | None = None, waiter: Waiter | None = None
) -> bool:
    """Retourne ``True`` si le DOM reste inchangé pendant ``timeout`` secondes."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    return w.wait_until_dom_is_stable(driver, timeout)


def wait_for_element(
    driver,
    by=By.ID,
    locator_value=None,
    condition=ec.presence_of_element_located,
    timeout: int | None = None,
    waiter: Waiter | None = None,
):
    """Attend qu'un élément réponde à ``condition``."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    return w.wait_for_element(driver, by, locator_value, condition, timeout)


def find_clickable(
    driver,
    by,
    locator_value,
    timeout: int | None = None,
    waiter: Waiter | None = None,
):
    """Retourne l'élément lorsqu'il devient cliquable."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    return w.find_clickable(driver, by, locator_value, timeout)


def find_visible(
    driver,
    by,
    locator_value,
    timeout: int | None = None,
    waiter: Waiter | None = None,
):
    """Retourne l'élément lorsqu'il est visible."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    return w.find_visible(driver, by, locator_value, timeout)


def find_present(
    driver,
    by,
    locator_value,
    timeout: int | None = None,
    waiter: Waiter | None = None,
):
    """Retourne l'élément dès qu'il est présent dans le DOM."""
    w = waiter or DEFAULT_WAITER
    w.wrapper.writer = write_log
    return w.find_present(driver, by, locator_value, timeout)


def wait_for_dom_after(func):
    """Decorator calling ``self.wait_for_dom`` after function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Exécute ``func`` puis attend que le DOM soit prêt."""
        result = func(*args, **kwargs)
        if args:
            instance = args[0]
            driver = args[1] if len(args) > 1 else kwargs.get("driver")
            if driver is not None and hasattr(instance, "wait_for_dom"):
                instance.wait_for_dom(driver)
        return result

    return wrapper
