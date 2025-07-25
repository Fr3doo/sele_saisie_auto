# resource_manager.py
"""Gestionnaire centralisé du navigateur et de la mémoire partagée."""

from __future__ import annotations

import sys

from sele_saisie_auto.automation import BrowserSession
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.encryption_utils import Credentials, EncryptionService
from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.logging_service import Logger

__all__ = ["ResourceManager"]


class ResourceManager:
    """Prépare et nettoie navigateur et mémoire pour l'automatisation."""

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
        self._app_config = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> ResourceManager:
        """Charge la configuration et prépare les services.

        Returns:
            ResourceManager: Instance prête à l'emploi.
        """

        self._app_config = self._config_manager.load()
        if self._session is None:
            self._session = BrowserSession(self.log_file, self._app_config)
        if hasattr(self._encryption_service, "__enter__"):
            self._enc_ctx = self._encryption_service.__enter__()
        else:
            self._enc_ctx = None
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Nettoie toutes les ressources ouvertes."""

        if self._driver is not None and self._session is not None:
            self._session.close()

        if hasattr(self._encryption_service, "__exit__"):
            self._encryption_service.__exit__(exc_type, exc, tb)

        if self._credentials is not None:
            for mem in (
                self._credentials.mem_key,
                self._credentials.mem_login,
                self._credentials.mem_password,
            ):
                if mem is not None:
                    try:
                        self._encryption_service.shared_memory_service.supprimer_memoire_partagee_securisee(
                            mem
                        )
                    except Exception:  # nosec B110 - cleanup best effort
                        pass
        self._credentials = None
        self._driver = None
        self._session = None

    def close(self) -> None:
        """Ferme explicitement les ressources en appelant ``__exit__``."""

        self.__exit__(None, None, None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def app_config(self):  # pragma: no cover - simple accessor
        return self._app_config

    @property
    def browser_session(self):  # pragma: no cover - simple accessor
        if self._session is None:
            raise RuntimeError("Resource manager not initialized")
        return self._session

    @property
    def encryption_service(self):  # pragma: no cover - simple accessor
        return self._encryption_service

    def get_credentials(self) -> Credentials:
        """Retourne les identifiants chiffrés stockés en mémoire partagée."""

        if self._credentials is None:
            self._credentials = self._encryption_service.retrieve_credentials()
        return self._credentials

    def initialize_shared_memory(self, logger: Logger | None = None) -> Credentials:
        """Retrieve credentials and ensure shared memory is initialized."""

        creds = self.get_credentials()
        if not all(
            [creds.mem_key, creds.mem_login, creds.mem_password]
        ):  # pragma: no cover - sanity check
            if logger:
                logger.error(
                    "🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés"
                )
            raise AutomationExitError(
                "La mémoire partagée n'a pas été initialisée correctement"
            )
        return creds

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
