from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_utils import (
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    wait_for_dom_ready,
    wait_until_dom_is_stable,
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

    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Launch the WebDriver and load the given URL."""
        write_log("Ouverture du navigateur", self.log_file, "DEBUG")
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

    def close(self) -> None:
        """Close the WebDriver if started."""
        if self.driver is not None:
            write_log("Fermeture du navigateur", self.log_file, "DEBUG")
            self.driver.quit()
            self.driver = None


class BrowserSession:
    """Encapsulate :class:`SeleniumDriverManager` for higher-level automation."""

    def __init__(
        self, log_file: str, app_config: AppConfig | None = None
    ) -> None:  # pragma: no cover - simple wiring
        self.log_file = log_file
        self.app_config = app_config
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

    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Open the browser and navigate to ``url``."""
        write_log("Ouverture du navigateur", self.log_file, "DEBUG")
        self.driver = self._manager.open(
            url,
            fullscreen=fullscreen,
            headless=headless,
            no_sandbox=no_sandbox,
        )
        return self.driver

    def close(self) -> None:
        """Close the browser if it was opened."""
        if self.driver is not None:
            write_log("Fermeture du navigateur", self.log_file, "DEBUG")
        self._manager.close()
        self.driver = None

    # ------------------------------------------------------------------
    # DOM helpers
    # ------------------------------------------------------------------
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
        wait_until_dom_is_stable(driver, timeout=default_timeout)
        wait_for_dom_ready(driver, long_timeout)
