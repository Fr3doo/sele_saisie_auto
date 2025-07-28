from sele_saisie_auto.app_config import AppConfig

from .service_configurator import ServiceConfigurator, Services, build_services


def service_configurator_factory(app_config: AppConfig) -> ServiceConfigurator:
    """Return a :class:`ServiceConfigurator` for ``app_config``."""

    return ServiceConfigurator.from_config(app_config)


__all__ = [
    "Services",
    "build_services",
    "ServiceConfigurator",
    "service_configurator_factory",
]
