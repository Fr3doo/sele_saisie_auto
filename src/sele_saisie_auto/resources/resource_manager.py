# src\sele_saisie_auto\resources\resource_manager.py
"""Gestionnaire centralisé du navigateur et de la mémoire partagée."""

from __future__ import annotations

from multiprocessing import shared_memory
from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.browser_session import create_session
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.encryption_utils import Credentials, EncryptionService
from sele_saisie_auto.exceptions import AutomationExitError, ResourceManagerInitError
from sele_saisie_auto.interfaces import BrowserSessionProtocol
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.resources.resource_context import ResourceContext

__all__ = ["ResourceManager"]


class ResourceManager:
    """Prépare et nettoie navigateur et mémoire pour l'automatisation."""

    def __init__(
        self,
        log_file: str,
        encryption_service: EncryptionService | None = None,
        *,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        """Initialise le gestionnaire.

        Args:
            log_file: Chemin du fichier de log.
        """

        self.log_file = log_file
        self._config_manager = ConfigManager(log_file)
        self._encryption_service = encryption_service or EncryptionService(
            log_file, memory_config=memory_config
        )
        self._resource_context = ResourceContext(
            log_file, self._encryption_service, memory_config=memory_config
        )
        self._credentials: Credentials | None = None
        self._session: BrowserSessionProtocol | None = None
        self._driver: WebDriver | None = None
        self._app_config: AppConfig | None = None
        self._res_ctx: ResourceContext | None = None

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> ResourceManager:
        """Charge la configuration et prépare les services.

        Returns:
            ResourceManager: Instance prête à l'emploi.
        """

        try:
            app_config = self._config_manager.load()
            self._app_config = app_config
            if self._session is None:
                self._session = create_session(app_config)
            if hasattr(self._resource_context, "__enter__"):
                self._res_ctx = self._resource_context.__enter__()
            else:
                self._res_ctx = None
        except Exception as exc:
            raise ResourceManagerInitError(str(exc)) from exc
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any | None,
    ) -> None:
        """Nettoie toutes les ressources ouvertes."""

        session = self._session
        if session is not None:
            if self._driver is not None:
                session.close()

        exit_ctx = getattr(self._resource_context, "__exit__", None)
        if exit_ctx is not None:
            handled_exc = exc if isinstance(exc, Exception) else None
            exit_ctx(exc_type, handled_exc, tb)

        self._cleanup_shared_memory(
            [
                getattr(self._credentials, "mem_key", None),
                getattr(self._credentials, "mem_login", None),
                getattr(self._credentials, "mem_password", None),
            ]
        )
        self._credentials = None
        self._driver = None
        self._session = None

    def _cleanup_shared_memory(
        self, memories: list[shared_memory.SharedMemory | None]
    ) -> None:
        """Close and unlink given shared memory segments."""

        for mem in memories:
            if mem is None:
                continue
            for action in ("close", "unlink"):
                try:
                    getattr(mem, action)()
                except (AttributeError, FileNotFoundError):
                    pass

    def close(self) -> None:
        """Ferme explicitement les ressources en appelant ``__exit__``.

        Cette méthode est **idempotente** : elle peut être invoquée
        plusieurs fois sans provoquer d'erreur ni rouvrir de ressources.
        """

        self.__exit__(None, None, None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def app_config(self) -> AppConfig | None:
        return self._app_config

    @property
    def browser_session(
        self,
    ) -> BrowserSessionProtocol:
        if self._session is None:
            raise RuntimeError("Resource manager not initialized")
        return self._session

    @property
    def encryption_service(
        self,
    ) -> EncryptionService:
        return self._encryption_service

    def get_credentials(self) -> Credentials:
        """Retourne les identifiants chiffrés stockés en mémoire partagée."""
        if self._credentials is None:
            self._credentials = self._resource_context.get_credentials()
        return self._credentials

    def read_credentials(self) -> tuple[str, str]:
        """Return decrypted credentials using the encryption service."""

        creds = self.get_credentials()
        aes_key, enc_login, enc_pwd = creds.get_auth_tuple()
        login = self._encryption_service.dechiffrer_donnees(enc_login, aes_key)
        password = self._encryption_service.dechiffrer_donnees(enc_pwd, aes_key)
        return login, password

    def initialize_shared_memory(self, logger: Logger | None = None) -> Credentials:
        """Retrieve credentials and ensure shared memory is initialized."""

        creds = self.get_credentials()
        if not all([creds.mem_key, creds.mem_login, creds.mem_password]):
            if logger:
                logger.error(
                    "🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés"
                )
            raise AutomationExitError(
                "La mémoire partagée n'a pas été initialisée correctement"
            )
        return creds

    def get_driver(
        self,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> WebDriver | None:
        """Ouvre le navigateur si besoin et retourne le ``WebDriver``."""

        if self._session is None:
            raise RuntimeError("Resource manager not initialized")
        if self._driver is None:
            if self._app_config is None:
                raise RuntimeError("Configuration application manquante")
            self._driver = self._session.open(
                self._app_config.url,
                headless=headless,
                no_sandbox=no_sandbox,
            )
        return self._driver
