from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.selenium_utils import send_keys_to_element


class LoginHandler:
    """Handle login steps for PSA Time."""

    def __init__(self, log_file: str | None = None) -> None:
        self.log_file = log_file

    def login(self, driver: WebDriver, credentials, encryption_service) -> None:
        """Fill username and password fields using decrypted credentials."""
        write_log("Déchiffrement des identifiants", self.log_file, "DEBUG")
        username = encryption_service.dechiffrer_donnees(
            credentials.login, credentials.aes_key
        )
        password = encryption_service.dechiffrer_donnees(
            credentials.password, credentials.aes_key
        )
        write_log("Envoi des identifiants", self.log_file, "DEBUG")
        send_keys_to_element(driver, By.ID, Locators.USERNAME.value, username)
        send_keys_to_element(driver, By.ID, Locators.PASSWORD.value, password)
        send_keys_to_element(driver, By.ID, Locators.PASSWORD.value, Keys.RETURN)
