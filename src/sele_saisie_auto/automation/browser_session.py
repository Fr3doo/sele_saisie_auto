# src\sele_saisie_auto\automation\browser_session.py
from __future__ import annotations

from typing import cast

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig, get_default_timeout
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.exceptions import DriverError
from sele_saisie_auto.interfaces import WaiterProtocol
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import (
    Waiter,
    click_element_without_wait,
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    send_keys_to_element,
    wait_for_dom_ready,
)
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter, get_waiter
from sele_saisie_auto.shared_utils import get_log_file
from sele_saisie_auto.timeouts import LONG_TIMEOUT


class SeleniumDriverManager:
    """Handle WebDriver lifecycle for the automation."""

    def __init__(self, log_file: str, app_config: AppConfig | None = None) -> None:
        self.log_file = log_file
        self.app_config = app_config
        self.driver: WebDriver | None = None

    def __enter__(self) -> SeleniumDriverManager:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        self.close()

    @handle_selenium_errors(default_return=None)
    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Launch the WebDriver and load the given URL."""
        write_log(format_message("BROWSER_OPEN", {}), self.log_file, "DEBUG")
        self.driver = ouvrir_navigateur_sur_ecran_principal(
            plein_ecran=fullscreen,
            url=url,
            headless=headless,
            no_sandbox=no_sandbox,
        )
        if self.driver is not None:
            self.driver = definir_taille_navigateur(self.driver, 1260, 800)
            timeout = self.app_config.long_timeout if self.app_config else LONG_TIMEOUT
            wait_for_dom_ready(self.driver, timeout)
        return self.driver

    @handle_selenium_errors(default_return=None)
    def close(self) -> None:
        """Close the WebDriver if started."""
        if self.driver is not None:
            write_log(format_message("BROWSER_CLOSE", {}), self.log_file, "DEBUG")
            self.driver.quit()
            self.driver = None


class BrowserSession:
    """Encapsulate :class:`SeleniumDriverManager` for higher-level automation."""

    def __init__(
        self,
        log_file: str,
        app_config: AppConfig | None = None,
        waiter: WaiterProtocol | None = None,
    ) -> None:
        self.log_file = log_file
        self.app_config = app_config
        self.waiter: WaiterProtocol
        if waiter is None:
            timeout = get_default_timeout(app_config)
            internal_waiter: Waiter = create_waiter(timeout)
            if app_config is not None and hasattr(app_config, "long_timeout"):
                internal_waiter.wrapper.long_timeout = app_config.long_timeout
            self.waiter = internal_waiter
        else:
            self.waiter = waiter
        if app_config is not None:
            self._manager = SeleniumDriverManager(log_file, app_config)
        else:
            self._manager = SeleniumDriverManager(log_file)
        self.driver: WebDriver | None = None

    def __enter__(self) -> BrowserSession:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        self.close()

    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Open the browser and navigate to ``url``."""
        write_log(format_message("BROWSER_OPEN", {}), self.log_file, "DEBUG")
        try:
            self.driver = self._manager.open(
                url,
                fullscreen=fullscreen,
                headless=headless,
                no_sandbox=no_sandbox,
            )
        except Exception as exc:  # noqa: BLE001
            write_log(
                f"❌ {messages.WEBDRIVER} : {exc}",
                self.log_file,
                "ERROR",
            )
            raise DriverError(f"Failed to start WebDriver: {exc}") from exc
        if self.driver is not None and hasattr(self.driver, "execute_script"):
            self.waiter.wait_for_dom_ready(
                self.driver,
                self.app_config.long_timeout if self.app_config else LONG_TIMEOUT,
            )
        return self.driver

    @handle_selenium_errors(default_return=None)
    def close(self) -> None:
        """Close the browser if it was opened."""
        if self.driver is not None:
            write_log(format_message("BROWSER_CLOSE", {}), self.log_file, "DEBUG")
        self._manager.close()
        self.driver = None

    # ------------------------------------------------------------------
    # DOM helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver: WebDriver, max_attempts: int | None = None) -> None:
        """Wait until the DOM is stable and fully loaded.

        Args:
            driver: Selenium WebDriver.
            max_attempts: Number of tries before raising ``RuntimeError`` if the
                DOM never stabilizes.
        """
        default_timeout = get_default_timeout(self.app_config)
        long_timeout = self.app_config.long_timeout if self.app_config else LONG_TIMEOUT
        attempt = 0
        attempts_limit = max_attempts if max_attempts is not None else 1
        raise_error = max_attempts is not None
        while attempt < attempts_limit:
            result = self.waiter.wait_until_dom_is_stable(
                driver, timeout=default_timeout
            )
            if result is not False:
                break
            attempt += 1
        else:
            if raise_error:
                write_log(messages.DOM_NOT_STABLE, self.log_file, "ERROR")
                raise RuntimeError(messages.DOM_NOT_STABLE)

        self.waiter.wait_for_dom_ready(driver, long_timeout)

    # ------------------------------------------------------------------
    # Element helpers
    # ------------------------------------------------------------------
    @handle_selenium_errors(default_return=False)
    def click(self, element_id: str) -> bool:
        """Click the element identified by ``element_id``."""

        if self.driver is None:
            return False

        click_element_without_wait(self.driver, cast(By, By.ID), element_id)
        return True

    @handle_selenium_errors(default_return=False)
    def fill_input(self, element_id: str, value: str) -> bool:
        """Send ``value`` to the input identified by ``element_id``."""

        if self.driver is None:
            return False

        send_keys_to_element(self.driver, cast(By, By.ID), element_id, value)
        return True

    # ------------------------------------------------------------------
    # Iframe helpers
    # ------------------------------------------------------------------
    @handle_selenium_errors(default_return=False)
    def go_to_iframe(self, id_or_name: str) -> bool:
        """Switch to the iframe identified by ``id_or_name``."""

        if self.driver is None:
            return False

        try:
            self.driver.switch_to.frame(self.driver.find_element(By.ID, id_or_name))
            return True
        except Exception:  # noqa: BLE001
            try:
                self.driver.switch_to.frame(
                    self.driver.find_element(By.NAME, id_or_name)
                )
                return True
            except Exception:  # noqa: BLE001
                return False

    @handle_selenium_errors(default_return=None)
    def go_to_default_content(self) -> None:
        """Return to the default document context."""

        if self.driver is None:
            return
        self.driver.switch_to.default_content()


def create_session(app_config: AppConfig) -> BrowserSession:
    """Create a :class:`BrowserSession` configured from ``app_config``."""

    return BrowserSession(get_log_file(), app_config, waiter=get_waiter(app_config))
