from sele_saisie_auto.app_config import AppConfig, AppConfigRaw
from sele_saisie_auto.selenium_utils import Waiter
from sele_saisie_auto.selenium_utils.waiter_factory import get_waiter


def test_get_waiter_returns_configured_waiter(sample_config):
    cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    waiter = get_waiter(cfg)

    assert isinstance(waiter, Waiter)
    assert waiter.wrapper.default_timeout == cfg.default_timeout
    assert waiter.wrapper.long_timeout == cfg.long_timeout
