from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

import sele_saisie_auto.selenium_utils.waiter_factory as WaiterFactory  # noqa: N812
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.decorators import handle_selenium_errors
from sele_saisie_auto.interfaces import WaiterProtocol
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import (
    Waiter,
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    wait_for_dom_ready,
)
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT, LONG_TIMEOUT


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
            timeout = (
                self.app_config.long_timeout
                if self.app_config
                else LONG_TIMEOUT  # pragma: no cover - fallback
            )
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
    ) -> None:  # pragma: no cover - simple wiring
        self.log_file = log_file
        self.app_config = app_config
        if waiter is None:
            self.waiter = WaiterFactory.get_waiter(app_config)
        else:
            self.waiter = waiter
        if app_config is not None:
            self._manager = SeleniumDriverManager(log_file, app_config)
        else:  # pragma: no cover - legacy path
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

    @handle_selenium_errors(default_return=None)
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
        self.driver = self._manager.open(
            url,
            fullscreen=fullscreen,
            headless=headless,
            no_sandbox=no_sandbox,
        )
        if self.driver is not None:  # pragma: no cover - simple branch
            self.waiter.wait_for_dom_ready(
                self.driver,
                self.app_config.long_timeout if self.app_config else LONG_TIMEOUT,
            )
        return self.driver

    @handle_selenium_errors(default_return=None)
    def close(self) -> None:
        """Close the browser if it was opened."""
        if self.driver is not None:  # pragma: no cover - simple branch
            write_log(format_message("BROWSER_CLOSE", {}), self.log_file, "DEBUG")
        self._manager.close()
        self.driver = None

    # ------------------------------------------------------------------
    # DOM helpers
    # ------------------------------------------------------------------
    @handle_selenium_errors(default_return=None)
    def wait_for_dom(self, driver) -> None:
        """Wait until the DOM is stable and fully loaded."""
        default_timeout = (
            self.app_config.default_timeout
            if self.app_config
            else DEFAULT_TIMEOUT  # pragma: no cover - fallback
        )
        long_timeout = (
            self.app_config.long_timeout
            if self.app_config
            else LONG_TIMEOUT  # pragma: no cover - fallback
        )
        self.waiter.wait_until_dom_is_stable(driver, timeout=default_timeout)
        self.waiter.wait_for_dom_ready(driver, long_timeout)

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
