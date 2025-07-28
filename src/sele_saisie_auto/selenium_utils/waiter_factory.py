"""Factory to create configured :class:`Waiter` instances."""

from __future__ import annotations

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.selenium_utils.wait_helpers import Waiter


def get_waiter(app_config: AppConfig | None) -> Waiter:
    """Return a :class:`Waiter` configured with ``app_config`` timeouts."""
    if app_config is None:
        return Waiter()
    from sele_saisie_auto.configuration import ServiceConfigurator

    configurator = ServiceConfigurator.from_config(app_config)
    return configurator.create_waiter()
