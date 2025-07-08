from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

import sele_saisie_auto.selenium_utils.waiter_factory as WaiterFactory  # noqa: N812
from sele_saisie_auto import messages
from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import Waiter, wait_for_dom_after
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class DateEntryPage:
    """Handle the timesheet date selection page."""

    def __init__(
        self, automation: PSATimeAutomation, waiter: Waiter | None = None
    ) -> None:
        self._automation = automation
        self.waiter = (
            waiter
            or getattr(automation, "waiter", None)
            or WaiterFactory.get_waiter(self.config)
        )
        self.alert_handler = AlertHandler(automation, waiter=self.waiter)

    @property
    def log_file(self) -> str:
        return self._automation.log_file

    @property
    def config(self) -> AppConfig:  # pragma: no cover - accessor
        ctx = getattr(self._automation, "context", None)
        cfg = getattr(ctx, "config", None)
        if cfg is None or not hasattr(cfg, "default_timeout"):
            return SimpleNamespace(
                default_timeout=DEFAULT_TIMEOUT,
                long_timeout=LONG_TIMEOUT,
            )  # pragma: no cover - fallback
        return cfg

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
    @handle_selenium_errors(default_return=False)
    def navigate_from_home_to_date_entry_page(self, driver):
        """Navigate from the home page to the date entry page."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.NAV_TO_DATE_ENTRY.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.NAV_TO_DATE_ENTRY.value
            )
        self.wait_for_dom(driver)

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.SIDE_MENU_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(
                driver, By.ID, Locators.SIDE_MENU_BUTTON.value
            )
        self.wait_for_dom(driver)

        return self.switch_to_main_frame(driver)

    @handle_selenium_errors(default_return=None)
    def handle_date_input(self, driver, date_cible):
        """Fill the date field with ``date_cible`` or next Saturday."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        date_input = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.DATE_INPUT.value,
            timeout=self.config.default_timeout,
        )
        if date_input:
            current_date_value = date_input.get_attribute("value")
            if date_cible and str(date_cible).strip():
                sap.modifier_date_input(date_input, date_cible, "Date cible appliquée")
            else:
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
                    sap.write_log(
                        format_message("NO_DATE_CHANGE", {}),
                        self.log_file,
                        "DEBUG",
                    )
        self.wait_for_dom(driver)

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def submit_date_cible(self, driver):
        """Validate the chosen date."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.ADD_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.send_keys_to_element(
                driver, By.ID, Locators.ADD_BUTTON.value, Keys.RETURN
            )
        self.wait_for_dom(driver)
        return element_present

    @handle_selenium_errors(default_return=None)
    def process_date(self, driver, date_cible) -> None:
        """Orchestrate date selection and validation."""

        self.handle_date_input(driver, date_cible)
        program_break_time(
            1,
            messages.WAIT_STABILISATION,
        )
        write_log(format_message("DOM_STABLE", {}), self.log_file, "DEBUG")
        if self.submit_date_cible(driver):
            self._handle_date_alert(driver)

    @handle_selenium_errors(default_return=None)
    def _handle_date_alert(self, driver) -> None:
        """Delegate alert handling to :class:`AlertHandler`."""

        self.alert_handler.handle_date_alert(driver)

    @handle_selenium_errors(default_return=None)
    def _click_action_button(self, driver, create_new: bool) -> None:
        """Click the appropriate action button on the page."""
        elem_id = (
            Locators.OK_BUTTON.value if create_new else Locators.COPY_TIME_BUTTON.value
        )
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            elem_id,
            ec.element_to_be_clickable,
            timeout=self.config.default_timeout,
        )
        if element_present:
            sap.click_element_without_wait(driver, By.ID, elem_id)
