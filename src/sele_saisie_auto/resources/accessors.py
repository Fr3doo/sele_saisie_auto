"""Simplified helpers to retrieve credentials and open a browser."""

from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.encryption_utils import Credentials, EncryptionService

__all__ = ["get_credentials", "get_driver"]


def get_credentials(encryption_service: EncryptionService) -> Credentials:
    """Return encrypted credentials using ``encryption_service``."""
    return encryption_service.retrieve_credentials()


def get_driver(
    browser_session: BrowserSession,
    url: str,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
):
    """Open the browser through ``browser_session`` and return the driver."""
    return browser_session.open(url, headless=headless, no_sandbox=no_sandbox)
