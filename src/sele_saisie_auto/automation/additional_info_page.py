from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.interfaces import WaiterProtocol
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.remplir_informations_supp_utils import ExtraInfoHelper
from sele_saisie_auto.selenium_utils import Waiter, wait_for_dom_after
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

if TYPE_CHECKING:
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class AdditionalInfoPage:
    """Handle the additional information modal."""

    @classmethod
    def from_automation(
        cls, automation: PSATimeAutomation, waiter: WaiterProtocol | None = None
    ) -> AdditionalInfoPage:
        """Create a page instance from a :class:`PSATimeAutomation`."""
        return cls(automation, waiter=waiter)

    def __init__(
        self, automation: PSATimeAutomation, waiter: WaiterProtocol | None = None
    ) -> None:
        self._automation = automation
        self.context = getattr(automation, "context", None)
        self.browser_session = getattr(automation, "browser_session", None)
        self._log_file = automation.log_file
        self.logger = automation.logger
        cfg = getattr(self.context, "config", None)
        if waiter is not None:
            self.waiter = waiter
        else:
            base_waiter = getattr(automation, "waiter", None)
            if base_waiter is not None:
                self.waiter = base_waiter
            else:
                timeout = (
                    cfg.default_timeout
                    if hasattr(cfg, "default_timeout")
                    else DEFAULT_TIMEOUT
                )
                self.waiter = create_waiter(timeout)
                if hasattr(cfg, "long_timeout"):
                    self.waiter.wrapper.long_timeout = cfg.long_timeout
        self.alert_handler = AlertHandler(automation, waiter=self.waiter)
        self.helper = ExtraInfoHelper(
            logger=self.logger,
            waiter=self.waiter,
            page=self,
            app_config=cfg if hasattr(cfg, "default_timeout") else None,
        )
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        sap.traiter_description = self.helper.traiter_description

    @property
    def log_file(self) -> str:
        return self._log_file

    @property
    def config(self) -> AppConfig:
        cfg = getattr(self.context, "config", None)
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
        if self.browser_session is not None:
            self.browser_session.go_to_default_content()
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
            switched_to_iframe = None
            if self.browser_session is not None:
                switched_to_iframe = self.browser_session.go_to_iframe(
                    Locators.MODAL_FRAME.value
                )

        if switched_to_iframe:
            descriptions = getattr(self.context, "descriptions", [])
            for config in descriptions:
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

    def log_information_details(self) -> None:
        """Log the extra information configuration details."""

        cfg = self.context.config

        write_log("👉 Infos_supp_cgi_periode_repos_respectee:", self.log_file, "DEBUG")
        for day, status in cfg.additional_information[
            "periode_repos_respectee"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Infos_supp_cgi_horaire_travail_effectif:", self.log_file, "DEBUG")
        for day, status in cfg.additional_information[
            "horaire_travail_effectif"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Planning de travail de la semaine:", self.log_file, "DEBUG")
        for day, status in cfg.additional_information[
            "plus_demi_journee_travaillee"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Infos_supp_cgi_duree_pause_dejeuner:", self.log_file, "DEBUG")
        for day, status in cfg.additional_information["duree_pause_dejeuner"].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")
