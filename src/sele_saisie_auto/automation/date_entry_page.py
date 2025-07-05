from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_utils import (
    DEFAULT_TIMEOUT,
    click_element_without_wait,
    modifier_date_input,
    send_keys_to_element,
    switch_to_default_content,
    wait_for_dom_after,
    wait_for_element,
)

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class DateEntryPage:
    """Handle the timesheet date selection page."""

    def __init__(self, automation: PSATimeAutomation) -> None:
        self._automation = automation

    @property
    def log_file(self) -> str:
        return self._automation.log_file

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver) -> None:
        """Delegate DOM wait to the parent automation."""
        self._automation.wait_for_dom(driver)

    def switch_to_main_frame(self, driver):
        """Switch to the main iframe using the parent automation."""
        return self._automation.switch_to_iframe_main_target_win0(driver)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @wait_for_dom_after
    def navigate_from_home_to_date_entry_page(self, driver):
        """Navigate from the home page to the date entry page."""
        element_present = wait_for_element(
            driver,
            By.ID,
            Locators.NAV_TO_DATE_ENTRY.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            click_element_without_wait(driver, By.ID, Locators.NAV_TO_DATE_ENTRY.value)
        self.wait_for_dom(driver)

        element_present = wait_for_element(
            driver,
            By.ID,
            Locators.SIDE_MENU_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            click_element_without_wait(driver, By.ID, Locators.SIDE_MENU_BUTTON.value)
        self.wait_for_dom(driver)

        return self.switch_to_main_frame(driver)

    def handle_date_input(self, driver, date_cible):
        """Fill the date field with ``date_cible`` or next Saturday."""
        date_input = wait_for_element(
            driver, By.ID, Locators.DATE_INPUT.value, timeout=DEFAULT_TIMEOUT
        )
        if date_input:
            current_date_value = date_input.get_attribute("value")
            if date_cible and str(date_cible).strip():
                from sele_saisie_auto import saisie_automatiser_psatime as sap

                sap.modifier_date_input(date_input, date_cible, "Date cible appliquée")
            else:
                from sele_saisie_auto import saisie_automatiser_psatime as sap

                new_date_value = sap.get_next_saturday_if_not_saturday(
                    current_date_value
                )
                if new_date_value != current_date_value:
                    sap.modifier_date_input(
                        date_input,
                        new_date_value,
                        "Prochain samedi appliqué",
                    )
                else:
                    write_log(
                        "Aucune modification de la date nécessaire.",
                        self.log_file,
                        "DEBUG",
                    )
        self.wait_for_dom(driver)

    @wait_for_dom_after
    def submit_date_cible(self, driver):
        """Validate the chosen date."""
        element_present = wait_for_element(
            driver,
            By.ID,
            Locators.ADD_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            send_keys_to_element(driver, By.ID, Locators.ADD_BUTTON.value, Keys.RETURN)
        self.wait_for_dom(driver)
        return element_present

    def _handle_date_alert(self, driver) -> None:
        """Close alert if the date already exists."""
        switch_to_default_content(driver)
        alerte = Locators.ALERT_CONTENT_0.value
        if wait_for_element(driver, By.ID, alerte, timeout=DEFAULT_TIMEOUT):
            click_element_without_wait(driver, By.ID, Locators.CONFIRM_OK.value)
            write_log(
                "\nERREUR : Vous avez déjà créé une feuille de temps pour cette période. (10502,125)",
                self.log_file,
                "INFO",
            )
            write_log(
                "--> Modifier la date du PSATime dans le fichier ini. Le programme va s'arreter.",
                self.log_file,
                "INFO",
            )
            sys.exit()
        else:
            write_log("Date validée avec succès.", self.log_file, "DEBUG")

    def _click_action_button(self, driver, create_new: bool) -> None:
        """Click the appropriate action button on the page."""
        elem_id = (
            Locators.OK_BUTTON.value if create_new else Locators.COPY_TIME_BUTTON.value
        )
        element_present = wait_for_element(
            driver,
            By.ID,
            elem_id,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            click_element_without_wait(driver, By.ID, elem_id)
