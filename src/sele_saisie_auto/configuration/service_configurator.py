from __future__ import annotations

from dataclasses import dataclass

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation import BrowserSession
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.selenium_utils import Waiter


@dataclass
class Services:
    """Bundle of commonly used automation services."""

    encryption_service: EncryptionService
    browser_session: BrowserSession
    waiter: Waiter


def build_services(app_config: AppConfig, log_file: str) -> Services:
    """Create configured service instances from ``app_config``."""
    waiter = Waiter(
        default_timeout=app_config.default_timeout,
        long_timeout=app_config.long_timeout,
    )
    browser_session = BrowserSession(log_file, app_config, waiter=waiter)
    encryption_service = EncryptionService(log_file)
    return Services(encryption_service, browser_session, waiter)
