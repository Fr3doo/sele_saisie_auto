import pytest

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw
from sele_saisie_auto.automation import LoginHandler
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.configuration import ServiceConfigurator, Services, build_services
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.selenium_utils import Waiter


def test_build_services(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    services = build_services(app_cfg, "log.html")

    assert isinstance(services, Services)
    assert isinstance(services.encryption_service, EncryptionService)
    assert isinstance(services.browser_session, BrowserSession)
    assert isinstance(services.waiter, Waiter)
    assert isinstance(services.login_handler, LoginHandler)
    assert services.browser_session.app_config is app_cfg
    assert services.browser_session.waiter is services.waiter


def test_build_services_operational(monkeypatch, sample_config, tmp_path):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))

    # avoid file system writes
    monkeypatch.setattr(
        "sele_saisie_auto.logger_utils.write_log",
        lambda *a, **k: None,
    )

    calls = {}

    class DummyManager:
        def __init__(self, log_file: str, app_config: AppConfig):
            calls["init"] = (log_file, app_config)

        def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
            calls["open"] = (url, fullscreen, headless, no_sandbox)
            return "driver"

        def close(self):
            calls["close"] = True

    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )

    services = build_services(app_cfg, str(tmp_path / "log.html"))

    assert services.waiter.wrapper.default_timeout == app_cfg.default_timeout
    assert services.waiter.wrapper.long_timeout == app_cfg.long_timeout

    wait_calls = {}
    monkeypatch.setattr(
        services.waiter,
        "wait_for_dom_ready",
        lambda driver, timeout: wait_calls.setdefault("ready", (driver, timeout)),
    )
    monkeypatch.setattr(
        services.waiter,
        "wait_until_dom_is_stable",
        lambda driver, timeout=None: wait_calls.setdefault("stable", (driver, timeout)),
    )

    driver = services.browser_session.open(app_cfg.url, headless=True)
    services.browser_session.wait_for_dom(driver)
    services.browser_session.close()

    assert driver == "driver"
    assert calls.get("open")[0] == app_cfg.url
    assert wait_calls["stable"] == ("driver", app_cfg.default_timeout)
    assert wait_calls["ready"] == ("driver", app_cfg.long_timeout)
    assert calls.get("close") is True

    key = services.encryption_service.generer_cle_aes()
    enc = services.encryption_service.chiffrer_donnees("msg", key)
    assert services.encryption_service.dechiffrer_donnees(enc, key) == "msg"
    assert len(key) == 32


def test_build_services_invalid_config(tmp_path):
    """Ensure ``build_services`` fails with an invalid ``AppConfig`` instance."""

    class Dummy:
        pass

    with pytest.raises(ValueError):
        build_services(Dummy(), str(tmp_path / "log.html"))


def test_create_methods(sample_config):
    """Ensure individual factory helpers return properly configured objects."""

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    configurator = ServiceConfigurator(app_cfg)

    waiter = configurator.create_waiter()
    assert isinstance(waiter, Waiter)
    assert waiter.wrapper.default_timeout == app_cfg.default_timeout
    assert waiter.wrapper.long_timeout == app_cfg.long_timeout

    browser_session = configurator.create_browser_session("log.html")
    assert isinstance(browser_session, BrowserSession)
    assert browser_session.app_config is app_cfg
    assert isinstance(browser_session.waiter, Waiter)

    enc_service = configurator.create_encryption_service("log.html")
    assert isinstance(enc_service, EncryptionService)


def test_service_configurator_build_services(sample_config):
    """Vérifie que ``ServiceConfigurator.build_services`` configure correctement les services."""

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    configurator = ServiceConfigurator(app_cfg)

    services = configurator.build_services("log.html")

    assert isinstance(services, Services)
    assert isinstance(services.encryption_service, EncryptionService)
    assert isinstance(services.browser_session, BrowserSession)
    assert isinstance(services.waiter, Waiter)
    assert isinstance(services.login_handler, LoginHandler)
    assert services.browser_session.app_config is app_cfg
    assert services.browser_session.waiter is services.waiter
    assert services.waiter.wrapper.default_timeout == app_cfg.default_timeout
    assert services.waiter.wrapper.long_timeout == app_cfg.long_timeout


def test_encryption_backend_injection(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))

    class DummyBackend:
        def __init__(self):
            self.called = False

        def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
            self.called = True
            return b"x" * taille_cle

        def chiffrer_donnees(
            self, donnees: str, cle: bytes, taille_bloc: int = 128
        ) -> bytes:
            return donnees.encode()

        def dechiffrer_donnees(
            self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
        ) -> str:
            return donnees_chiffrees.decode()

    backend = DummyBackend()
    configurator = ServiceConfigurator(app_cfg, encryption_backend=backend)
    enc_service = configurator.create_encryption_service("log.html")

    key = enc_service.generer_cle_aes()
    assert backend.called
    assert key == b"x" * 32
