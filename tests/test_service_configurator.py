from sele_saisie_auto.app_config import AppConfig, AppConfigRaw
from sele_saisie_auto.automation import BrowserSession
from sele_saisie_auto.configuration import Services, build_services
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.selenium_utils import Waiter


def test_build_services(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    services = build_services(app_cfg, "log.html")

    assert isinstance(services, Services)
    assert isinstance(services.encryption_service, EncryptionService)
    assert isinstance(services.browser_session, BrowserSession)
    assert isinstance(services.waiter, Waiter)
    assert services.browser_session.app_config is app_cfg
    assert services.browser_session.waiter is services.waiter
