from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.interfaces import BrowserSessionProtocol
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import format_message, write_log
from sele_saisie_auto.selenium_utils import send_keys_to_element, wait_for_dom_after

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation


class LoginHandler:
    """Handle login steps for PSA Time."""

    @classmethod
    def from_automation(cls, automation: PSATimeAutomation) -> LoginHandler:
        """Create a new instance using an automation context."""
        return cls(
            automation.log_file,
            automation.encryption_service,
            automation.browser_session,
        )

    def __init__(
        self,
        log_file: str | None,
        encryption_service: EncryptionService,
        browser_session: BrowserSessionProtocol,
    ) -> None:
        self.log_file = log_file
        self.encryption_service = encryption_service
        self.browser_session = browser_session

    def wait_for_dom(self, driver: WebDriver) -> None:
        """Delegate DOM wait to :class:`BrowserSession`."""
        self.browser_session.wait_for_dom(driver)

    def login(self, driver: WebDriver, credentials) -> None:
        """Fill username and password fields using decrypted credentials."""
        write_log(format_message("DECRYPT_CREDENTIALS", {}), self.log_file, "DEBUG")
        username = self.encryption_service.dechiffrer_donnees(
            credentials.login, credentials.aes_key
        )
        password = self.encryption_service.dechiffrer_donnees(
            credentials.password, credentials.aes_key
        )
        write_log(format_message("SEND_CREDENTIALS", {}), self.log_file, "DEBUG")
        send_keys_to_element(driver, By.ID, Locators.USERNAME.value, username)
        send_keys_to_element(driver, By.ID, Locators.PASSWORD.value, password)
        send_keys_to_element(driver, By.ID, Locators.PASSWORD.value, Keys.RETURN)

    @wait_for_dom_after
    def connect_to_psatime(
        self,
        driver: WebDriver,
        cle_aes: bytes,
        nom_utilisateur_chiffre: bytes,
        mot_de_passe_chiffre: bytes,
    ) -> None:
        """Connecte l'utilisateur au portail PSATime."""
        creds = SimpleNamespace(
            aes_key=cle_aes,
            login=nom_utilisateur_chiffre,
            password=mot_de_passe_chiffre,
        )
        self.login(driver, creds)
