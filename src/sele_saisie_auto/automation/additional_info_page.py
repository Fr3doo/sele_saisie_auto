from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.remplir_informations_supp_utils import ExtraInfoHelper
from sele_saisie_auto.selenium_utils import Waiter, wait_for_dom_after
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

if TYPE_CHECKING:
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class AdditionalInfoPage:
    """Handle the additional information modal."""

    def __init__(
        self, automation: PSATimeAutomation, waiter: Waiter | None = None
    ) -> None:
        self._automation = automation
        ctx = getattr(self._automation, "context", None)
        cfg = getattr(ctx, "config", None)
        self.waiter = waiter or getattr(automation, "waiter", None) or Waiter()
        self.alert_handler = AlertHandler(automation, waiter=self.waiter)
        self.helper = ExtraInfoHelper(
            logger=self._automation.logger,
            waiter=self.waiter,
            page=self,
            app_config=cfg if hasattr(cfg, "default_timeout") else None,
        )
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        sap.traiter_description = self.helper.traiter_description

    @property
    def log_file(self) -> str:
        return self._automation.log_file

    @property
    def config(self) -> AppConfig:
        ctx = getattr(self._automation, "context", None)
        cfg = getattr(ctx, "config", None)
        if cfg is None or not hasattr(cfg, "default_timeout"):
            return SimpleNamespace(
                default_timeout=DEFAULT_TIMEOUT,
                long_timeout=LONG_TIMEOUT,
            )
        return cfg

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver) -> None:
        self._automation.wait_for_dom(driver)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @wait_for_dom_after
    @handle_selenium_errors(default_return=None)
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Open the modal to fill additional informations."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        self.wait_for_dom(driver)
        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.ADDITIONAL_INFO_LINK.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.ADDITIONAL_INFO_LINK.value
            )
        self._automation.browser_session.go_to_default_content()
        self.wait_for_dom(driver)

    @wait_for_dom_after
    @handle_selenium_errors(default_return=None)
    def submit_and_validate_additional_information(self, driver):
        """Fill all additional info fields and validate the modal."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.MODAL_FRAME.value,
            timeout=self.config.default_timeout,
        )
        if element_present:
            switched_to_iframe = self._automation.browser_session.go_to_iframe(
                Locators.MODAL_FRAME.value
            )

        if switched_to_iframe:
            for config in self._automation.context.descriptions:
                sap.traiter_description(driver, config)
            write_log(
                format_message("ADDITIONAL_INFO_DONE", {}),
                self.log_file,
                "INFO",
            )

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.SAVE_ICON.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(driver, By.ID, Locators.SAVE_ICON.value)

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def save_draft_and_validate(self, driver):
        """Click the save draft button and wait for completion."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.SAVE_DRAFT_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.SAVE_DRAFT_BUTTON.value
            )
            self.wait_for_dom(driver)
            self._handle_save_alerts(driver)
        return element_present

    @handle_selenium_errors(default_return=None)
    def _handle_save_alerts(self, driver) -> None:
        """Dismiss any alert shown after saving."""

        self.alert_handler.handle_alerts(driver, "save_alerts")
