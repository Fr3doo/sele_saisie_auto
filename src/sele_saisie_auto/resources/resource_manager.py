# resource_manager.py
"""Gestionnaire de contexte pour le chiffrement et la session navigateur."""

from __future__ import annotations

from sele_saisie_auto.automation import BrowserSession
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.encryption_utils import Credentials, EncryptionService

__all__ = ["ResourceManager"]


class ResourceManager:
    """Centralise les ressources lourdes nécessaires à l'automatisation."""

    def __init__(self, log_file: str) -> None:
        """Initialise le gestionnaire.

        Args:
            log_file: Chemin du fichier de log.
        """

        self.log_file = log_file
        self._config_manager = ConfigManager(log_file)
        self._encryption_service = EncryptionService(log_file)
        self._session: BrowserSession | None = None
        self._credentials: Credentials | None = None
        self._driver = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> ResourceManager:
        """Charge la configuration et prépare les services.

        Returns:
            ResourceManager: Instance prête à l'emploi.
        """

        self._app_config = self._config_manager.load()
        self._session = BrowserSession(self.log_file, self._app_config)
        self._enc_ctx = self._encryption_service.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Nettoie toutes les ressources ouvertes."""

        if self._driver is not None and self._session is not None:
            self._session.close()
        self._encryption_service.__exit__(exc_type, exc, tb)
        self._credentials = None
        self._driver = None
        self._session = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_credentials(self) -> Credentials:
        """Retourne les identifiants chiffrés stockés en mémoire partagée."""

        if self._credentials is None:
            self._credentials = self._encryption_service.retrieve_credentials()
        return self._credentials

    def get_driver(self, *, headless: bool = False, no_sandbox: bool = False):
        """Ouvre le navigateur si besoin et retourne le ``WebDriver``."""

        if self._session is None:
            raise RuntimeError("Resource manager not initialized")
        if self._driver is None:
            self._driver = self._session.open(
                self._app_config.url,
                headless=headless,
                no_sandbox=no_sandbox,
            )
        return self._driver
