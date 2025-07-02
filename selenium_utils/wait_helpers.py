"""Selenium wait helper functions."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import DEFAULT_TIMEOUT, LOG_FILE, write_log


def is_document_complete(driver):
    """Return True when the DOM is fully loaded."""
    return driver.execute_script("return document.readyState") == "complete"


def wait_for_dom_ready(driver, timeout=20):
    """Wait until the DOM is fully loaded."""
    WebDriverWait(driver, timeout).until(is_document_complete)
    write_log("DOM chargé avec succès.", LOG_FILE, "DEBUG")


def wait_until_dom_is_stable(driver, timeout=10):
    """Wait until the DOM stays unchanged for a short period."""
    previous_dom_snapshot = ""
    unchanged_count = 0
    required_stability_count = 3

    for _ in range(timeout):
        current_dom_snapshot = driver.page_source

        if current_dom_snapshot == previous_dom_snapshot:
            unchanged_count += 1
        else:
            unchanged_count = 0

        if unchanged_count >= required_stability_count:
            write_log("Le DOM est stable.", LOG_FILE, "DEBUG")
            return True

        previous_dom_snapshot = current_dom_snapshot
        time.sleep(1)

    write_log(
        "Le DOM n'est pas complètement stable après le délai.", LOG_FILE, "WARNING"
    )
    return False


def wait_for_element(
    driver,
    by=By.ID,
    locator_value=None,
    condition=EC.presence_of_element_located,
    timeout=10,
):
    """Wait for an element to satisfy a condition or return None."""
    if locator_value is None:
        write_log(
            "❌ Erreur : Le paramètre 'locator_value' doit être spécifié pour localiser l'élément.",
            LOG_FILE,
            "ERROR",
        )
        return None

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


def find_clickable(driver, by, locator_value, timeout=DEFAULT_TIMEOUT):
    """Return element when it becomes clickable."""
    return wait_for_element(
        driver, by, locator_value, EC.element_to_be_clickable, timeout
    )


def find_visible(driver, by, locator_value, timeout=DEFAULT_TIMEOUT):
    """Return element when it is visible."""
    return wait_for_element(
        driver,
        by,
        locator_value,
        EC.visibility_of_element_located,
        timeout,
    )


def find_present(driver, by, locator_value, timeout=DEFAULT_TIMEOUT):
    """Return element when it is present in the DOM."""
    return wait_for_element(
        driver, by, locator_value, EC.presence_of_element_located, timeout
    )
