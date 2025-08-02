from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.memory_config import MemoryConfig

from .service_configurator import ServiceConfigurator, Services, build_services


def service_configurator_factory(
    app_config: AppConfig, *, memory_config: MemoryConfig | None = None
) -> ServiceConfigurator:
    """Return a :class:`ServiceConfigurator` for ``app_config``."""

    return ServiceConfigurator.from_config(app_config, memory_config=memory_config)


__all__ = [
    "Services",
    "build_services",
    "ServiceConfigurator",
    "service_configurator_factory",
]
