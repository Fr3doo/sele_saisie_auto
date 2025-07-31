import sys
from pathlib import Path

import pytest

from sele_saisie_auto import console_ui
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.orchestration import AutomationOrchestrator
from tests.test_saisie_automatiser_psatime import DummyBrowserSession

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import types  # noqa: E402

from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402

pytestmark = pytest.mark.slow
from sele_saisie_auto.locators import Locators  # noqa: E402


class DummyEnc:
    def __init__(self):
        self.removed = []
        self.cle_aes = b"k" * 32

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def retrieve_credentials(self):
        return sap.Credentials(
            aes_key=self.cle_aes,
            mem_key=object(),
            login=b"user",
            mem_login=object(),
            password=b"pass",
            mem_password=object(),
        )

    def dechiffrer_donnees(self, data, key):
        return data.decode() if isinstance(data, bytes) else data

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)

    def remove_shared_memory(self, mem):
        self.supprimer_memoire_partagee_securisee(mem)


class DummySHMService:
    def __init__(self):
        self.removed = []

    def recuperer_de_memoire_partagee(self, name, size):
        return object(), b"k" * size

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)

    def remove_shared_memory(self, mem):
        self.supprimer_memoire_partagee_securisee(mem)


class DummyManager:
    def __init__(self, log_file):
        self.log_file = log_file
        self.driver = "driver"

    def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
        return self.driver

    def close(self):
        self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def setup_init(monkeypatch, cfg):
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "SharedMemoryService", lambda logger: DummySHMService())
    from sele_saisie_auto.configuration import Services
    from sele_saisie_auto.resources import resource_manager as rm
    from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter

    class DummyConfigurator:
        def __init__(self, cfg_b):
            self.cfg = cfg_b
            self.app_config = cfg_b

        def build_services(self, lf_b):
            waiter = create_waiter(self.cfg.default_timeout)
            session = sap.BrowserSession(lf_b, self.cfg, waiter=waiter)
            enc = DummyEnc()
            login = sap.LoginHandler(lf_b, enc, session)
            return Services(enc, session, waiter, login)

    monkeypatch.setattr(
        sap, "service_configurator_factory", lambda cfg_b: DummyConfigurator(cfg_b)
    )
    waiter = create_waiter(app_cfg.default_timeout)
    monkeypatch.setattr(
        rm,
        "ConfigManager",
        lambda log_file: types.SimpleNamespace(load=lambda: app_cfg),
    )
    monkeypatch.setattr(
        rm,
        "create_session",
        lambda cfg=app_cfg: DummyBrowserSession("log.html", cfg, waiter=waiter),
    )
    monkeypatch.setattr(
        sap,
        "ResourceManager",
        lambda log_file: rm.ResourceManager(log_file, DummyEnc()),
    )
    auto = sap.PSATimeAutomation("log.html", app_cfg)
    service_configurator = ServiceConfigurator(app_cfg)
    orch = AutomationOrchestrator.from_components(
        auto.resource_manager,
        auto.page_navigator,
        service_configurator,
        auto.context,
        auto.logger,
        choix_user=True,
    )
    auto.orchestrator = orch
    monkeypatch.setattr(sap, "_AUTOMATION", auto, raising=False)
    monkeypatch.setattr(sap, "_ORCHESTRATOR", orch, raising=False)
    monkeypatch.setattr(sap, "context", auto.context, raising=False)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )


def test_connect_to_psatime(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    actions = []
    from sele_saisie_auto.automation import login_handler as lh

    monkeypatch.setattr(
        lh,
        "send_keys_to_element",
        lambda driver, by, ident, value: actions.append((ident, value)),
    )
    sap.context.encryption_service = DummyEnc()
    sap._AUTOMATION.login_handler.browser_session.wait_for_dom = (
        lambda d: actions.append("dom")
    )
    sap._AUTOMATION.login_handler.connect_to_psatime("drv", b"key", b"user", b"pass")
    assert (Locators.USERNAME.value, "user") in actions
    assert (Locators.PASSWORD.value, "pass") in actions
    assert "dom" in actions


def test_switch_to_iframe(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    calls = []
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: True
    )
    monkeypatch.setattr(
        sap.BrowserSession,
        "go_to_iframe",
        lambda *a, **k: calls.append("sw") or True,
    )
    monkeypatch.setattr(
        sap._ORCHESTRATOR,
        "wait_for_dom",
        lambda *a, **k: calls.append("dom"),
    )
    assert sap._ORCHESTRATOR.switch_to_iframe_main_target_win0("drv") is True
    assert "sw" in calls
    assert "dom" in calls


def test_submit_date_cible(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._ORCHESTRATOR.date_entry_page,
        "submit_date_cible",
        lambda driver: called.setdefault("done", True) or True,
    )
    assert sap._ORCHESTRATOR.submit_date_cible("drv") is True
    assert called["done"] is True


def test_navigation_pages(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.date_entry_page,
        "navigate_from_home_to_date_entry_page",
        lambda driver: called.setdefault("nav", True),
    )
    assert sap._ORCHESTRATOR.navigate_from_home_to_date_entry_page("drv") is True
    assert called["nav"] is True


def test_additional_information(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "submit_and_validate_additional_information",
        lambda driver: called.setdefault("done", True),
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap._ORCHESTRATOR.submit_and_validate_additional_information("drv")
    assert called["done"] is True


def test_save_draft_and_validate(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "save_draft_and_validate",
        lambda driver: called.setdefault("done", True) or True,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap._ORCHESTRATOR.save_draft_and_validate("drv") is True
    assert called["done"] is True


def test_cleanup_resources(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = []
    manager = types.SimpleNamespace(close=lambda: called.append("close"))
    enc = DummyEnc()
    sap.context.encryption_service = enc
    shm_service = DummySHMService()
    sap.context.shared_memory_service = shm_service
    sap._ORCHESTRATOR.browser_session = manager
    sap._ORCHESTRATOR._cleanup_callback = (
        lambda mk, ml, mp: sap._AUTOMATION.cleanup_resources(manager, mk, ml, mp)
    )
    sap._ORCHESTRATOR.cleanup_resources("c", "n", "p")
    assert shm_service.removed == ["c", "n", "p"]
    assert "close" in called


EXCEPTIONS = [
    NoSuchElementException("boom"),
    TimeoutException("boom"),
    WebDriverException("boom"),
    Exception("boom"),
]


def test_main_exceptions(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    sap._AUTOMATION.choix_user = True
    monkeypatch.setattr(sap, "log_initialisation", lambda: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "initialize_shared_memory",
        lambda self: sap.Credentials(
            aes_key=b"k",
            mem_key=object(),
            login=b"user",
            mem_login=object(),
            password=b"pass",
            mem_password=object(),
        ),
    )
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: True
    )
    monkeypatch.setattr(sap, "modifier_date_input", lambda *a, **k: None)
    monkeypatch.setattr(sap.BrowserSession, "go_to_iframe", lambda *a, **k: True)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    monkeypatch.setattr(sap._ORCHESTRATOR, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(
        sap._AUTOMATION.browser_session.waiter,
        "wait_until_dom_is_stable",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        sap._AUTOMATION.browser_session.waiter,
        "wait_for_dom_ready",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(sap, "program_break_time", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.remplir_jours_feuille_de_temps.TimeSheetHelper,
        "run",
        lambda self, drv: None,
    )
    monkeypatch.setattr(sap, "traiter_description", lambda *a, **k: None)
    monkeypatch.setattr(sap, "detecter_doublons_jours", lambda *a, **k: None)
    monkeypatch.setattr(sap, "seprateur_menu_affichage_console", lambda: None)
    monkeypatch.setattr(
        console_ui,
        "ask_continue",
        lambda *a, **k: (_ for _ in ()).throw(ValueError()),
    )
    cleanup = {}
    monkeypatch.setattr(
        sap.BrowserSession,
        "close",
        lambda self: cleanup.setdefault("done", True),
    )
    monkeypatch.setattr(
        DummyBrowserSession,
        "close",
        lambda self: cleanup.setdefault("done", True),
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "run",
        lambda self, headless=False, no_sandbox=False: cleanup.setdefault("done", True),
    )
    for exc in EXCEPTIONS:
        monkeypatch.setattr(
            sap.LoginHandler,
            "connect_to_psatime",
            lambda *a, exc=exc, **k: (_ for _ in ()).throw(exc),
        )
        sap.main("log.html")
        sap._ORCHESTRATOR.cleanup_resources(None, None, None)
    assert cleanup["done"] is True
