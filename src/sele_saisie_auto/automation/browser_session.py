from __future__ import annotations

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_driver_manager import SeleniumDriverManager


class BrowserSession:
    """Encapsulate :class:`SeleniumDriverManager` for higher-level automation."""

    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        self._manager = SeleniumDriverManager(log_file)
        self.driver: Optional[WebDriver] = None

    def __enter__(self) -> "BrowserSession":
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
    ) -> Optional[WebDriver]:
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
