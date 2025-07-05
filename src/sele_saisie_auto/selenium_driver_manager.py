from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_utils import (
    LONG_TIMEOUT,
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    wait_for_dom_ready,
)


class SeleniumDriverManager:
    """Handle WebDriver lifecycle for the automation."""

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        self.driver: WebDriver | None = None

    def __enter__(self) -> SeleniumDriverManager:
        """Return itself when used as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        """Ensure the driver is closed when leaving a context."""
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
            wait_for_dom_ready(self.driver, LONG_TIMEOUT)
        return self.driver

    def close(self) -> None:
        """Close the WebDriver if started."""
        if self.driver is not None:
            write_log("Fermeture du navigateur", self.log_file, "DEBUG")
            self.driver.quit()
            self.driver = None
