from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.remplir_informations_supp_utils import ExtraInfoHelper
from sele_saisie_auto.selenium_utils import wait_for_dom_after
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class AdditionalInfoPage:
    """Handle the additional information modal."""

    def __init__(self, automation: PSATimeAutomation) -> None:
        self._automation = automation
        self.helper = ExtraInfoHelper(page=self)
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        sap.traiter_description = self.helper.traiter_description

    @property
    def log_file(self) -> str:
        return self._automation.log_file

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver) -> None:
        self._automation.wait_for_dom(driver)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Open the modal to fill additional informations."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        self.wait_for_dom(driver)
        element_present = sap.wait_for_element(
            driver,
            By.ID,
            Locators.ADDITIONAL_INFO_LINK.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.ADDITIONAL_INFO_LINK.value
            )
        sap.switch_to_default_content(driver)
        self.wait_for_dom(driver)

    @wait_for_dom_after
    def submit_and_validate_additional_information(self, driver):
        """Fill all additional info fields and validate the modal."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = sap.wait_for_element(
            driver, By.ID, Locators.MODAL_FRAME.value, timeout=DEFAULT_TIMEOUT
        )
        if element_present:
            switched_to_iframe = sap.switch_to_iframe_by_id_or_name(
                driver, Locators.MODAL_FRAME.value
            )

        if switched_to_iframe:
            for config in self._automation.context.descriptions:
                sap.traiter_description(driver, config)
            write_log(
                "Validation des informations supplémentaires terminée.",
                self.log_file,
                "INFO",
            )

        element_present = sap.wait_for_element(
            driver,
            By.ID,
            Locators.SAVE_ICON.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            sap.click_element_without_wait(driver, By.ID, Locators.SAVE_ICON.value)

    @wait_for_dom_after
    def save_draft_and_validate(self, driver):
        """Click the save draft button and wait for completion."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = sap.wait_for_element(
            driver,
            By.ID,
            Locators.SAVE_DRAFT_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.SAVE_DRAFT_BUTTON.value
            )
            self.wait_for_dom(driver)
        return element_present

    def _handle_save_alerts(self, driver) -> None:
        """Dismiss any alert shown after saving."""
        alerts = [
            Locators.ALERT_CONTENT_1.value,
            Locators.ALERT_CONTENT_2.value,
            Locators.ALERT_CONTENT_3.value,
        ]
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        sap.switch_to_default_content(driver)
        for alerte in alerts:
            if sap.wait_for_element(driver, By.ID, alerte, timeout=DEFAULT_TIMEOUT):
                sap.click_element_without_wait(driver, By.ID, Locators.CONFIRM_OK.value)
                write_log(
                    "⚠️ Alerte rencontrée lors de la sauvegarde.",
                    self.log_file,
                    "INFO",
                )
                break
