from __future__ import annotations

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from logger_utils import write_log
from selenium_utils import (
    LONG_TIMEOUT,
    definir_taille_navigateur,
    ouvrir_navigateur_sur_ecran_principal,
    wait_for_dom_ready,
)


class SeleniumDriverManager:
    """Handle WebDriver lifecycle for the automation."""

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        self.driver: Optional[WebDriver] = None

    def open(
        self,
        url: str,
        *,
        fullscreen: bool = False,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> Optional[WebDriver]:
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
