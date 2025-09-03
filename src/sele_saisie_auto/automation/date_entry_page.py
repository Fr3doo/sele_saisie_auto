# src\sele_saisie_auto\automation\date_entry_page.py
from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec

from sele_saisie_auto import messages
from sele_saisie_auto.alerts import AlertHandler
from sele_saisie_auto.app_config import AppConfig, get_default_timeout
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.interfaces import WaiterProtocol
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import wait_for_dom_after
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time

if TYPE_CHECKING:
    from sele_saisie_auto.navigation import PageNavigator
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class DateEntryPage:
    """Handle the timesheet date selection page."""

    def __init__(
        self,
        automation: PSATimeAutomation,
        *,
        page_navigator: PageNavigator | None = None,
        waiter: WaiterProtocol | None = None,
    ) -> None:
        self._automation = automation
        self.page_navigator = page_navigator
        if waiter is not None:
            self.waiter = waiter
        else:
            base_waiter = getattr(automation, "waiter", None)
            if base_waiter is not None:
                self.waiter = base_waiter
            else:
                timeout = get_default_timeout(self.config)
                self.waiter = create_waiter(timeout)
                if hasattr(self.config, "long_timeout"):
                    self.waiter.wrapper.long_timeout = self.config.long_timeout
        self.alert_handler = AlertHandler(automation, waiter=self.waiter)

    @property
    def log_file(self) -> str:
        return self._automation.log_file

    @property
    def config(self) -> AppConfig | Any:
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
    def wait_for_dom(self, driver: WebDriver, max_attempts: int | None = None) -> None:
        """Delegate DOM wait to the parent automation."""
        self._automation.wait_for_dom(driver, max_attempts=max_attempts)

    def switch_to_main_frame(self, driver: WebDriver) -> WebDriver | Any:
        """Switch to the main iframe using the parent automation."""
        return self._automation.switch_to_iframe_main_target_win0(driver)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def navigate_from_home_to_date_entry_page(self, driver: WebDriver) -> Any:
        """Navigate from the home page to the date entry page."""
        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.NAV_TO_DATE_ENTRY.value,
            ec.element_to_be_clickable,
            timeout=get_default_timeout(self.config),
        )
        if element_present:
            session = getattr(self._automation, "browser_session", None)
            if session is not None:
                session.click(Locators.NAV_TO_DATE_ENTRY.value)
        self.wait_for_dom(driver)

        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.SIDE_MENU_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=get_default_timeout(self.config),
        )
        if element_present:
            session = getattr(self._automation, "browser_session", None)
            if session is not None:
                session.click(Locators.SIDE_MENU_BUTTON.value)
        self.wait_for_dom(driver)

        return self.switch_to_main_frame(driver)

    @handle_selenium_errors(default_return=None)
    def handle_date_input(self, driver: WebDriver, date_cible: str | None) -> None:
        """Fill the date field with ``date_cible`` or next Saturday."""
        from sele_saisie_auto import saisie_automatiser_psatime as sap

        date_input = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.DATE_INPUT.value,
            timeout=get_default_timeout(self.config),
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
                    write_log(
                        format_message("NO_DATE_CHANGE", {}),
                        self.log_file,
                        "DEBUG",
                    )
        self.wait_for_dom(driver)

    @wait_for_dom_after
    @handle_selenium_errors(default_return=False)
    def submit_date_cible(self, driver: WebDriver) -> bool:
        """Validate the chosen date."""
        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            Locators.ADD_BUTTON.value,
            ec.element_to_be_clickable,
            timeout=get_default_timeout(self.config),
        )
        if element_present:
            session = getattr(self._automation, "browser_session", None)
            if session is not None:
                session.fill_input(Locators.ADD_BUTTON.value, Keys.RETURN)
        self.wait_for_dom(driver)
        return bool(element_present)

    @handle_selenium_errors(default_return=None)
    def process_date(self, driver: WebDriver, date_cible: str | None) -> bool | None:
        """Orchestrate date selection and validation.

        Returns ``False`` if a conflicting date alert was detected,
        ``True`` if submission succeeded without alert, ``None`` otherwise.
        """

        self.handle_date_input(driver, date_cible)
        program_break_time(
            1,
            messages.WAIT_STABILISATION,
        )
        write_log(format_message("DOM_STABLE", {}), self.log_file, "DEBUG")
        if self.submit_date_cible(driver):
            try:
                self._handle_date_alert(driver)
            except AutomationExitError:
                return False
            return True
        return None

    def _handle_date_alert(self, driver: WebDriver) -> None:
        """Delegate alert handling to :class:`AlertHandler`."""

        self.alert_handler.handle_date_alert(driver)

    def _click_if_present(self, driver: WebDriver, elem_id: str) -> bool:
        """Click ``elem_id`` if present and return success."""
        element_present = self.waiter.wait_for_element(
            driver,
            By.ID,
            elem_id,
            ec.element_to_be_clickable,
            timeout=get_default_timeout(self.config),
        )
        if element_present:
            session = getattr(self._automation, "browser_session", None)
            if session is not None:
                session.click(elem_id)
            return True
        return False

    @handle_selenium_errors(default_return=None)
    def _click_action_button(self, driver: WebDriver) -> None:
        """Click the default action button on the page."""
        self._click_if_present(driver, Locators.OK_BUTTON.value)

    @handle_selenium_errors(default_return=None)
    def click_creation_mode(self, driver: WebDriver) -> None:
        """Clique 'Ouvrir déclaration vide' si présent (fallback: 'Copie feuille temps')."""
        self.wait_for_dom(driver)
        self.switch_to_main_frame(driver)
        if self._click_if_present(driver, Locators.OK_BUTTON.value):
            return
        self._click_if_present(driver, Locators.COPY_TIME_BUTTON.value)
