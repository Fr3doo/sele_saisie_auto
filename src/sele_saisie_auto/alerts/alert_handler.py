# src\sele_saisie_auto\alerts\alert_handler.py
from __future__ import annotations

from configparser import ConfigParser
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw
from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import click_element_without_wait
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT

if TYPE_CHECKING:  # pragma: no cover
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation
    from sele_saisie_auto.selenium_utils.wait_helpers import Waiter


class AlertHandler:
    """Central handler for confirmation alerts."""

    #: Mapping of alert groups to the element identifiers composing them
    alert_configs = {
        "save_alerts": [
            Locators.ALERT_CONTENT_1.value,
            Locators.ALERT_CONTENT_2.value,
            Locators.ALERT_CONTENT_3.value,
        ],
        "date_alerts": [Locators.ALERT_CONTENT_0.value],
    }

    def __init__(
        self, automation: PSATimeAutomation, waiter: "Waiter" | None = None
    ) -> None:
        self._automation = automation
        self.context = getattr(automation, "context", None)
        self.browser_session = getattr(automation, "browser_session", None)
        self._log_file = automation.log_file
        if waiter is None:
            cfg = getattr(self.context, "config", None)
            app_cfg = (
                AppConfig.from_raw(AppConfigRaw(cfg))
                if isinstance(cfg, ConfigParser)
                else None
            )
            timeout = DEFAULT_TIMEOUT
            if app_cfg is not None and hasattr(app_cfg, "default_timeout"):
                timeout = app_cfg.default_timeout
            self.waiter = create_waiter(timeout)
            if app_cfg is not None and hasattr(app_cfg, "long_timeout"):
                self.waiter.wrapper.long_timeout = app_cfg.long_timeout
        else:
            self.waiter = waiter

    # ------------------------------------------------------------------
    # Common properties
    # ------------------------------------------------------------------
    @property
    def log_file(self) -> str:  # pragma: no cover - passthrough
        return self._log_file

    @property
    def config(self) -> AppConfig | Any:  # pragma: no cover - accessor
        cfg = getattr(self.context, "config", None)
        if cfg is None or not hasattr(cfg, "default_timeout"):
            return SimpleNamespace(
                default_timeout=DEFAULT_TIMEOUT,
                long_timeout=LONG_TIMEOUT,
            )  # pragma: no cover - fallback
        return cfg

    # ------------------------------------------------------------------
    # Alert helpers
    # ------------------------------------------------------------------
    def handle_date_alert(self, driver: WebDriver) -> None:
        """Close alert if the date already exists.

        Raises
        ------
        AutomationExitError
            If a conflicting date alert was found and closed.
        """
        if self.browser_session is not None:
            self.browser_session.go_to_default_content()
        for alerte in self.alert_configs.get("date_alerts", []):
            if self.waiter.wait_for_element(
                driver, By.ID, alerte, timeout=self.config.default_timeout
            ):
                click_element_without_wait(driver, By.ID, Locators.CONFIRM_OK.value)
                write_log(
                    format_message("TIME_SHEET_EXISTS_ERROR", {}),
                    self.log_file,
                    "INFO",
                )
                write_log(
                    format_message("MODIFY_DATE_MESSAGE", {}),
                    self.log_file,
                    "INFO",
                )
                raise AutomationExitError(format_message("TIME_SHEET_EXISTS_ERROR", {}))

        write_log(format_message("DATE_VALIDATED", {}), self.log_file, "DEBUG")

    def handle_save_alerts(self, driver: WebDriver) -> None:
        """Dismiss any alert shown after saving."""
        alerts = self.alert_configs.get("save_alerts", [])
        if self.browser_session is not None:
            self.browser_session.go_to_default_content()
        for alerte in alerts:
            if self.waiter.wait_for_element(
                driver, By.ID, alerte, timeout=self.config.default_timeout
            ):
                click_element_without_wait(driver, By.ID, Locators.CONFIRM_OK.value)
                write_log(
                    format_message("SAVE_ALERT_WARNING", {}),
                    self.log_file,
                    "INFO",
                )
                break

    def handle_alerts(self, driver: WebDriver, alert_type: str = "save_alerts") -> None:
        """General wrapper to dispatch alert handling.

        Parameters
        ----------
        driver:
            Selenium driver instance used for the interaction.
        alert_type:
            Type of alert to process. ``"save_alerts"`` (default) will
            look for confirmation alerts after saving. ``"date_alert"``
            will check for a conflict when submitting a date.
        """

        handlers = {
            "save_alerts": self.handle_save_alerts,
            "date_alert": self.handle_date_alert,
        }

        handler = handlers.get(alert_type)
        if handler is None:
            raise ValueError(f"Unknown alert_type: {alert_type}")
        return handler(driver)
