#src\sele_saisie_auto\selenium_utils\wait_helpers.py
"""Selenium wait helper functions."""

from __future__ import annotations

import inspect
import time
from functools import wraps
from typing import Any, Callable, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

from . import get_default_logger
from . import wrapper as _wrapper

Wrapper = _wrapper.Wrapper
is_document_complete = _wrapper.is_document_complete
# expose WebDriverWait for monkeypatching in tests

# ------------------------------------------------------------------
# Monkey-patches utiles aux tests.  Les attributs n’existent pas dans
# les stubs → on ignore l’avertissement « attr-defined ».
# ------------------------------------------------------------------
WebDriverWait = _wrapper.WebDriverWait  # type: ignore[attr-defined]
_wrapper.time = time  # type: ignore[attr-defined]


class Waiter:
    """Utility object encapsulating explicit wait helpers."""

    def __init__(
        self,
        default_timeout: int = DEFAULT_TIMEOUT,
        long_timeout: int = LONG_TIMEOUT,
        wrapper: Wrapper | None = None,
        logger: Logger | None = None,
    ) -> None:  # pragma: no cover - simple initializer
        """Configure les délais d'attente par défaut."""
        self.logger = logger or get_default_logger()
        self.wrapper: Wrapper = wrapper or Wrapper(
            default_timeout,
            long_timeout,
            logger=self.logger,
        )

    def wait_for_dom_ready(self, driver: WebDriver, timeout: int | None = None) -> None:
        """Wait until the DOM is fully loaded."""
        self.wrapper.wait_for_dom_ready(driver, timeout)

    def wait_until_dom_is_stable(self, driver: WebDriver, timeout: int | None = None) -> bool:
        """Return True when the DOM remains unchanged for ``timeout`` seconds."""
        return self.wrapper.wait_until_dom_is_stable(driver, timeout)

    def wait_for_element(
        self,
        driver: WebDriver,
        by: str = By.ID,
        locator_value: Optional[str] = None,
        condition: Callable[[tuple[str, str]], Any] = ec.presence_of_element_located,
        timeout: Optional[int] = None,
    ) -> Optional[WebElement]:
        """Wait for an element to satisfy ``condition`` or return ``None``."""
        return self.wrapper.wait_for_element(
            driver,
            by,
            locator_value,
            condition,
            timeout,
        )

    # Convenience wrappers -------------------------------------------------
    def find_clickable(self, driver: WebDriver, by: str, locator_value: Optional[str] = None, timeout: Optional[int] = None) -> Optional[WebElement]:
        """Return element when it becomes clickable."""
        return self.wrapper.find_clickable(driver, by, locator_value, timeout)

    def find_visible(self, driver: WebDriver, by: str, locator_value: Optional[str] = None, timeout: Optional[int] = None) -> Optional[WebElement]:
        """Return element when it is visible."""
        return self.wrapper.find_visible(driver, by, locator_value, timeout)

    def find_present(self, driver: WebDriver, by: str, locator_value: Optional[str] = None, timeout: Optional[int] = None) -> Optional[WebElement]:
        """Return element when it is present in the DOM."""
        return self.wrapper.find_present(driver, by, locator_value, timeout)


DEFAULT_WAITER = Waiter()


def wait_for_dom_ready(
    driver : WebDriver,
    timeout: int | None = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> None:
    """Wait until the DOM is fully loaded."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    w.wait_for_dom_ready(driver, timeout)


def wait_until_dom_is_stable(
    driver : WebDriver,
    timeout: int | None = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> bool:
    """Retourne ``True`` si le DOM reste inchangé pendant ``timeout`` secondes."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    return w.wait_until_dom_is_stable(driver, timeout)


def wait_for_element(
    driver : WebDriver,
    by: str = By.ID,
    locator_value: Optional[str] = None,
    condition: Callable[[tuple[str, str]], Any] = ec.presence_of_element_located,
    timeout: int | None = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> Optional[WebElement]:
    """Attend qu'un élément réponde à ``condition``."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    return w.wait_for_element(driver, by, locator_value, condition, timeout)


def find_clickable(
    driver : WebDriver,
    by: str = By.ID,
    locator_value: Optional[str] = None,
    timeout: Optional[int] = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> Optional[WebElement]:
    """Retourne l'élément lorsqu'il devient cliquable."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    return w.find_clickable(driver, by, locator_value, timeout)


def find_visible(
    driver: WebDriver,
    by: str = By.ID,
    locator_value: Optional[str] = None,
    timeout: Optional[int] = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> Optional[WebElement]:
    """Retourne l'élément lorsqu'il est visible."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    return w.find_visible(driver, by, locator_value, timeout)


def find_present(
    driver: WebDriver,
    by: str = By.ID,
    locator_value: Optional[str] = None,
    timeout: Optional[int] = None,
    waiter: Waiter | None = None,
    logger: Logger | None = None,
) -> Optional[WebElement]:
    """Retourne l'élément dès qu'il est présent dans le DOM."""
    w = waiter or DEFAULT_WAITER
    if logger is not None:
        w.logger = logger
        w.wrapper.logger = logger
    return w.find_present(driver, by, locator_value, timeout)


def wait_for_dom_after(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator calling ``self.wait_for_dom`` after function execution."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Exécute ``func`` puis attend que le DOM soit prêt."""
        result = func(*args, **kwargs)
        if args:
            instance = args[0]
            driver = kwargs.get("driver")
            if driver is None:
                signature = inspect.signature(func)
                if "driver" in signature.parameters:
                    index = list(signature.parameters).index("driver")
                    if len(args) > index:
                        driver = args[index]
            if driver is not None and hasattr(instance, "wait_for_dom"):
                instance.wait_for_dom(driver)
        return result

    return wrapper
