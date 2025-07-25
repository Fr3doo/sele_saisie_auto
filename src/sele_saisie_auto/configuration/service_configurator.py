from __future__ import annotations

from dataclasses import dataclass

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation import BrowserSession
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.interfaces import BrowserSessionProtocol, WaiterProtocol
from sele_saisie_auto.selenium_utils import Waiter


@dataclass
class Services:
    """Bundle of commonly used automation services."""

    encryption_service: EncryptionService
    browser_session: BrowserSessionProtocol
    waiter: WaiterProtocol


class ServiceConfigurator:
    """Configure core services based on :class:`AppConfig`."""

    def __init__(self, app_config: AppConfig) -> None:
        self.app_config = app_config

    def create_encryption_service(self, log_file: str) -> EncryptionService:
        """Return a new :class:`EncryptionService`."""

        return EncryptionService(log_file)

    def create_waiter(self) -> Waiter:
        """Return a configured :class:`Waiter`."""

        return Waiter(
            default_timeout=self.app_config.default_timeout,
            long_timeout=self.app_config.long_timeout,
        )

    def create_browser_session(self, log_file: str) -> BrowserSessionProtocol:
        """Return a new :class:`BrowserSession`."""

        return BrowserSession(log_file, self.app_config, waiter=self.create_waiter())

    def build_services(self, log_file: str) -> Services:
        """Convenient helper returning all core services."""

        waiter = self.create_waiter()
        browser_session = BrowserSession(log_file, self.app_config, waiter=waiter)
        encryption_service = EncryptionService(log_file)
        return Services(encryption_service, browser_session, waiter)


def build_services(app_config: AppConfig, log_file: str) -> Services:
    """Instancier et retourner les services principaux de l'application.

    Ce constructeur configure un :class:`Waiter` selon les valeurs fournies
    par ``app_config`` puis initialise ``BrowserSession`` et
    ``EncryptionService`` avec le même fichier de log. Les instances sont
    renvoyées regroupées dans la dataclass :class:`Services` afin de partager
    facilement ces outils entre les différentes étapes de l'automatisation.

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
        ``browser_session`` et ``waiter`` prêts à être utilisés.
    """
    waiter: WaiterProtocol = Waiter(
        default_timeout=app_config.default_timeout,
        long_timeout=app_config.long_timeout,
    )
    browser_session: BrowserSessionProtocol = BrowserSession(
        log_file, app_config, waiter=waiter
    )
    encryption_service: EncryptionService = EncryptionService(log_file)
    return Services(encryption_service, browser_session, waiter)


__all__ = ["Services", "build_services", "ServiceConfigurator"]
