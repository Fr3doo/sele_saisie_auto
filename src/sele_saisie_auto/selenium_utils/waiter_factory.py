"""Utility to create configured :class:`Waiter` objects."""

from __future__ import annotations

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.selenium_utils.wait_helpers import Waiter
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT


def create_waiter(timeout: int) -> Waiter:
    """Return a :class:`Waiter` using ``timeout`` for its delays."""
    return Waiter(default_timeout=timeout, long_timeout=timeout * 2)


def get_waiter(app_config: AppConfig | None) -> Waiter:
    """Return a :class:`Waiter` configured from ``app_config``."""
    timeout = DEFAULT_TIMEOUT
    long_timeout = DEFAULT_TIMEOUT * 2
    if app_config is not None:
        timeout = getattr(app_config, "default_timeout", DEFAULT_TIMEOUT)
        long_timeout = getattr(app_config, "long_timeout", timeout * 2)
    return Waiter(default_timeout=timeout, long_timeout=long_timeout)


__all__ = ["create_waiter", "get_waiter"]
