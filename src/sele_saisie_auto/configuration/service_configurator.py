from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import cast

from sele_saisie_auto.app_config import AppConfig, get_default_timeout
from sele_saisie_auto.automation import LoginHandler
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.encryption_utils import (
    DefaultEncryptionBackend,
    EncryptionBackend,
    EncryptionService,
)
from sele_saisie_auto.interfaces import (
    BrowserSessionProtocol,
    LoginHandlerProtocol,
    WaiterProtocol,
)
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.selenium_utils import Waiter


@dataclass
class Services:
    """Bundle of commonly used automation services."""

    encryption_service: EncryptionService
    browser_session: BrowserSessionProtocol
    waiter: WaiterProtocol
    login_handler: LoginHandlerProtocol


class ServiceConfigurator:
    """Configure core services based on :class:`AppConfig`."""

    @classmethod
    def from_config(
        cls, app_config: AppConfig, *, memory_config: MemoryConfig | None = None
    ) -> ServiceConfigurator:
        """Return a configurator for ``app_config``."""

        return cls(app_config, memory_config=memory_config)

    def __init__(
        self,
        app_config: AppConfig,
        encryption_backend: EncryptionBackend | None = None,
        login_handler_cls: (
            Callable[
                [str | None, EncryptionService, BrowserSessionProtocol],
                LoginHandlerProtocol,
            ]
            | None
        ) = None,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        self._validate_app_config(app_config)
        self.app_config = app_config
        self.encryption_backend = encryption_backend
        self.login_handler_cls = login_handler_cls or LoginHandler
        self.memory_config = memory_config or MemoryConfig()

    # --------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------
    @staticmethod
    def _validate_app_config(cfg: AppConfig) -> None:
        """Ensure all required fields of ``AppConfig`` are present."""

        required = [
            f.name
            for f in fields(AppConfig)
            if f.name not in {"encrypted_login", "encrypted_mdp", "date_cible", "raw"}
        ]
        missing = [name for name in required if not hasattr(cfg, name)]
        if missing:
            raise ValueError(
                "Champs manquants dans AppConfig: " + ", ".join(sorted(missing))
            )

    def create_encryption_service(self, log_file: str) -> EncryptionService:
        """Return a new :class:`EncryptionService`."""

        backend = self.encryption_backend or DefaultEncryptionBackend(log_file)
        return EncryptionService(
            log_file,
            backend=backend,
            memory_config=self.memory_config,
        )

    def create_waiter(self) -> Waiter:
        """Return a configured :class:`Waiter`."""

        return Waiter(
            default_timeout=get_default_timeout(self.app_config),
            long_timeout=self.app_config.long_timeout,
        )

    def create_browser_session(self, log_file: str) -> BrowserSessionProtocol:
        """Return a new :class:`BrowserSession`."""

        return cast(
            BrowserSessionProtocol,
            BrowserSession(log_file, self.app_config, waiter=self.create_waiter()),
        )

    def create_login_handler(
        self,
        log_file: str,
        encryption_service: EncryptionService,
        browser_session: BrowserSessionProtocol,
    ) -> LoginHandlerProtocol:
        """Return a new :class:`LoginHandler`."""

        return cast(
            LoginHandlerProtocol,
            self.login_handler_cls(log_file, encryption_service, browser_session),
        )

    def build_services(self, log_file: str) -> Services:
        """Convenient helper returning all core services."""

        waiter = self.create_waiter()
        browser_session = BrowserSession(log_file, self.app_config, waiter=waiter)
        encryption_service = self.create_encryption_service(log_file)
        login_handler = self.create_login_handler(
            log_file, encryption_service, browser_session
        )
        return Services(
            encryption_service,
            cast(BrowserSessionProtocol, browser_session),
            waiter,
            login_handler,
        )


def build_services(
    app_config: AppConfig,
    log_file: str,
    encryption_backend: EncryptionBackend | None = None,
    memory_config: MemoryConfig | None = None,
) -> Services:
    """Instancier et retourner les services principaux de l'application.

    Ce constructeur configure un :class:`Waiter` selon les valeurs fournies
    par ``app_config`` puis initialise ``BrowserSession``,
    ``EncryptionService`` et ``LoginHandler`` avec le même fichier de log.
    Les instances sont renvoyées regroupées dans la dataclass :class:`Services`
    afin de partager facilement ces outils entre les différentes étapes de
    l'automatisation.

    Parameters
    ----------
    app_config : AppConfig
        Configuration de l'application utilisée pour paramétrer les services.
    log_file : str
        Chemin vers le fichier de log commun aux services.

    Returns
    -------
    Services
        Instance de :class:`Services` regroupant ``encryption_service``,
        ``browser_session``, ``waiter`` et ``login_handler`` prêts à être utilisés.
    """
    configurator = ServiceConfigurator(
        app_config, encryption_backend, memory_config=memory_config
    )
    return configurator.build_services(log_file)


__all__ = ["Services", "build_services", "ServiceConfigurator"]
