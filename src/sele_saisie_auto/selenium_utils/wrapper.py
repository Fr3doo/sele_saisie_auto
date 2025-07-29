# src\sele_saisie_auto\selenium_utils\wrapper.py
"""High level wrapper around WebDriver wait helpers."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, cast

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from sele_saisie_auto import messages
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

from . import get_default_logger


def is_document_complete(driver: WebDriver) -> bool:
    """Return ``True`` when the DOM is fully loaded."""
    execute_script = cast(Callable[[str], Any], driver.execute_script)
    ready_state: str = cast(str, execute_script("return document.readyState"))
    return ready_state == "complete"


class Wrapper:
    """Utility object exposing common waiting helpers."""

    def __init__(
        self,
        default_timeout: int = DEFAULT_TIMEOUT,
        long_timeout: int = LONG_TIMEOUT,
        logger: Logger | None = None,
    ) -> None:
        self.default_timeout = default_timeout
        self.long_timeout = long_timeout
        self.logger = logger or get_default_logger()

    # ------------------------------------------------------------------
    # DOM helpers
    # ------------------------------------------------------------------
    def wait_for_dom_ready(self, driver: WebDriver, timeout: int | None = None) -> None:
        """Wait until the DOM is fully loaded."""
        timeout = timeout or self.long_timeout
        WebDriverWait(driver, timeout).until(is_document_complete)
        self.logger.debug("DOM chargé avec succès.")

    def wait_until_dom_is_stable(
        self, driver: WebDriver, timeout: int | None = None
    ) -> bool:
        """Return ``True`` if the DOM remains unchanged for ``timeout`` seconds."""
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
                self.logger.debug(messages.DOM_STABLE)
                return True

            previous_dom_snapshot = current_dom_snapshot
            time.sleep(1)

        self.logger.warning(messages.DOM_NOT_STABLE)
        return False

    # ------------------------------------------------------------------
    # Element helpers
    # ------------------------------------------------------------------
    def wait_for_element(
        self,
        driver: WebDriver,
        by: str = By.ID,
        locator_value: Optional[str] = None,
        condition: Callable[[tuple[str, str]], Any] = ec.presence_of_element_located,
        timeout: Optional[int] = None,
    ) -> Optional[WebElement]:
        """Wait for an element to satisfy ``condition`` or return ``None``."""
        if locator_value is None:
            self.logger.error(messages.LOCATOR_VALUE_REQUIRED)
            return None

        timeout = timeout or self.default_timeout
        found_elements = driver.find_elements(by, locator_value)
        if found_elements:
            matched_element: WebElement = cast(
                WebElement,
                WebDriverWait(driver, timeout).until(condition((by, locator_value))),
            )
            self.logger.debug(
                f"Élément avec {by}='{locator_value}' trouvé et condition '{condition.__name__}' validée."
            )
            return matched_element

        self.logger.warning(
            f"Élément avec {by}='{locator_value}' non trouvé dans le délai imparti ({timeout}s)."
        )
        return None

    def find_clickable(
        self,
        driver: WebDriver,
        by: str = By.ID,
        locator_value: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[WebElement]:
        """Return the element when it becomes clickable."""
        return self.wait_for_element(
            driver, by, locator_value, ec.element_to_be_clickable, timeout
        )

    def find_visible(
        self,
        driver: WebDriver,
        by: str = By.ID,
        locator_value: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[WebElement]:
        """Return the element when it is visible."""
        return self.wait_for_element(
            driver, by, locator_value, ec.visibility_of_element_located, timeout
        )

    def find_present(
        self,
        driver: WebDriver,
        by: str = By.ID,
        locator_value: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[WebElement]:
        """Return the element once it is present in the DOM."""
        return self.wait_for_element(
            driver, by, locator_value, ec.presence_of_element_located, timeout
        )


DEFAULT_WRAPPER = Wrapper()
