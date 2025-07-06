"""Selenium wait helper functions."""

from __future__ import annotations

import time
from functools import wraps

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from sele_saisie_auto import messages
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

from . import LOG_FILE, write_log


class Waiter:
    """Utility object encapsulating explicit wait helpers."""

    def __init__(
        self, default_timeout: int = DEFAULT_TIMEOUT, long_timeout: int = LONG_TIMEOUT
    ) -> None:  # pragma: no cover - simple initializer
        """Configure les délais d'attente par défaut."""
        self.default_timeout = default_timeout
        self.long_timeout = long_timeout

    def wait_for_dom_ready(self, driver, timeout: int | None = None):
        """Wait until the DOM is fully loaded."""
        timeout = timeout or self.long_timeout
        WebDriverWait(driver, timeout).until(is_document_complete)
        write_log("DOM chargé avec succès.", LOG_FILE, "DEBUG")

    def wait_until_dom_is_stable(self, driver, timeout: int | None = None) -> bool:
        """Return True when the DOM remains unchanged for ``timeout`` seconds."""
        previous_dom_snapshot = ""
        unchanged_count = 0
        required_stability_count = 3

        timeout = timeout or self.default_timeout
        for _ in range(timeout):
            current_dom_snapshot = driver.page_source

            if current_dom_snapshot == previous_dom_snapshot:
                unchanged_count += 1
            else:
                unchanged_count = 0

            if unchanged_count >= required_stability_count:
                write_log(messages.DOM_STABLE, LOG_FILE, "DEBUG")
                return True

            previous_dom_snapshot = current_dom_snapshot
            time.sleep(1)

        write_log(
            messages.DOM_NOT_STABLE,
            LOG_FILE,
            "WARNING",
        )
        return False

    def wait_for_element(
        self,
        driver,
        by=By.ID,
        locator_value=None,
        condition=ec.presence_of_element_located,
        timeout: int | None = None,
    ):
        """Wait for an element to satisfy ``condition`` or return ``None``."""
        if locator_value is None:
            write_log(
                messages.LOCATOR_VALUE_REQUIRED,
                LOG_FILE,
                "ERROR",
            )
            return None

        timeout = timeout or self.default_timeout
        found_elements = driver.find_elements(by, locator_value)
        if found_elements:
            matched_element = WebDriverWait(driver, timeout).until(
                condition((by, locator_value))
            )
            write_log(
                f"Élément avec {by}='{locator_value}' trouvé et condition '{condition.__name__}' validée.",
                LOG_FILE,
                "DEBUG",
            )
            return matched_element

        write_log(
            f"Élément avec {by}='{locator_value}' non trouvé dans le délai imparti ({timeout}s).",
            LOG_FILE,
            "WARNING",
        )
        return None

    # Convenience wrappers -------------------------------------------------
    def find_clickable(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it becomes clickable."""
        return self.wait_for_element(
            driver, by, locator_value, ec.element_to_be_clickable, timeout
        )

    def find_visible(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it is visible."""
        return self.wait_for_element(
            driver, by, locator_value, ec.visibility_of_element_located, timeout
        )

    def find_present(self, driver, by, locator_value, timeout: int | None = None):
        """Return element when it is present in the DOM."""
        return self.wait_for_element(
            driver, by, locator_value, ec.presence_of_element_located, timeout
        )


DEFAULT_WAITER = Waiter()


def is_document_complete(driver):
    """Return True when the DOM is fully loaded."""
    return driver.execute_script("return document.readyState") == "complete"


def wait_for_dom_ready(
    driver, timeout: int | None = None, waiter: Waiter | None = None
):
    """Wait until the DOM is fully loaded."""
    w = waiter or DEFAULT_WAITER
    w.wait_for_dom_ready(driver, timeout)


def wait_until_dom_is_stable(
    driver, timeout: int | None = None, waiter: Waiter | None = None
) -> bool:
    """Retourne ``True`` si le DOM reste inchangé pendant ``timeout`` secondes."""
    w = waiter or DEFAULT_WAITER
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
