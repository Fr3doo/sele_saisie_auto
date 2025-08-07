import sys
import types
from pathlib import Path

import pytest

from sele_saisie_auto import console_ui
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.utils import misc as utils_misc

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import sele_saisie_auto.cli as cli  # noqa: E402
import sele_saisie_auto.logger_utils as logger_utils  # noqa: E402
from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402
from sele_saisie_auto.logger_utils import afficher_message_insertion  # noqa: E402
from sele_saisie_auto.memory_config import MemoryConfig  # noqa: E402
from tests.conftest import FakeEncryptionService  # noqa: E402

# Les tests de ce module s'appuient sur l'orchestrateur refactorisé
# `AutomationOrchestrator` afin de valider le nouveau fonctionnement.

pytestmark = pytest.mark.slow


class DummySHMService:
    def __init__(self):
        self.removed = []

    def recuperer_de_memoire_partagee(self, name, size):
        return object(), b"k" * size

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)

    def remove_shared_memory(self, mem):
        self.supprimer_memoire_partagee_securisee(mem)


class DummySHM:
    def __init__(self, name):
        self.name = name
        if "nom" in name:
            self.buf = bytearray(b"user")
        else:
            self.buf = bytearray(b"pass")

    def close(self):
        pass

    def unlink(self):
        pass


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


class DummyBrowserSession(BrowserSession):
    def __init__(self, log_file, app_config=None, waiter=None):
        # Do not call super().__init__ to avoid heavy setup
        self.log_file = log_file
        self.app_config = app_config
        self.open_calls = []
        self.driver = types.SimpleNamespace(page_source="")
        self.waiter = waiter

    def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
        self.open_calls.append((url, fullscreen, headless, no_sandbox))
        return self.driver

    def go_to_iframe(self, ident):
        self.go_calls = getattr(self, "go_calls", [])
        self.go_calls.append(ident)
        return True

    def go_to_default_content(self):
        self.default_called = True

    def close(self):
        self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class DummyLoginHandler:
    def __init__(self, log_file, enc, session):
        self.log_file = log_file
        self.calls = []

    def connect_to_psatime(self, driver, key, login, pwd):
        self.calls.append((driver, key, login, pwd))


class DummyDateEntryPage:
    def __init__(self, automation, waiter=None):
        self.automation = automation
        self.calls = []

    def navigate_from_home_to_date_entry_page(self, driver):
        self.calls.append("nav")
        return True

    def handle_date_input(self, driver, date):
        self.calls.append(("handle", date))

    def process_date(self, driver, date):
        self.calls.append(("process", date))

    def submit_date_cible(self, driver):
        self.calls.append("submit")
        return True


class DummyAdditionalInfoPage:
    def __init__(self, automation, waiter=None):
        self.automation = automation
        self.calls = []
        sap.traiter_description = lambda *a, **k: None
        self.alert_handler = types.SimpleNamespace(
            handle_alerts=lambda d, alert_type="save_alerts": self.calls.append(
                (d, alert_type)
            )
        )

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append("nav_add")
        return True

    def submit_and_validate_additional_information(self, driver):
        self.calls.append("submit_add")
        return True

    def save_draft_and_validate(self, driver):
        self.calls.append("save")
        return True

    def _handle_save_alerts(self, driver):
        self.alert_handler.handle_alerts(driver, "save_alerts")

    def log_information_details(self):
        self.calls.append("log_info")


def setup_init(monkeypatch, cfg, *, patch_services: bool = True):
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw, get_default_timeout

    app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "SharedMemoryService", lambda logger: DummySHMService())
    monkeypatch.setattr(sap, "LoginHandler", DummyLoginHandler)
    monkeypatch.setattr(sap, "DateEntryPage", DummyDateEntryPage)
    monkeypatch.setattr(sap, "AdditionalInfoPage", DummyAdditionalInfoPage)
    monkeypatch.setattr(
        cli,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": "user")
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": "pass")
    from sele_saisie_auto.resources import resource_manager as rm

    if patch_services:
        from sele_saisie_auto.configuration import Services
        from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter

        class DummyConfigurator:
            def __init__(self, cfg_b):
                self.cfg = cfg_b
                self.app_config = cfg_b

            def build_services(self, lf_b):
                waiter = create_waiter(get_default_timeout(self.cfg))
                session = sap.BrowserSession(lf_b, self.cfg, waiter=waiter)
                enc = FakeEncryptionService()
                login = sap.LoginHandler(lf_b, enc, session)
                return Services(enc, session, waiter, login)

        monkeypatch.setattr(
            sap,
            "service_configurator_factory",
            lambda cfg_b, **kw: DummyConfigurator(cfg_b),
        )
        waiter = create_waiter(get_default_timeout(app_cfg))
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
            lambda log_file, **kw: rm.ResourceManager(
                log_file, FakeEncryptionService()
            ),
        )
    else:
        monkeypatch.setattr(
            sap,
            "ResourceManager",
            lambda log_file, **kw: rm.ResourceManager(
                log_file, FakeEncryptionService()
            ),
        )
    auto = sap.PSATimeAutomation("log.html", app_cfg)
    service_configurator = ServiceConfigurator(app_cfg)
    orch = AutomationOrchestrator.from_components(
        auto.resource_manager,
        auto.page_navigator,
        service_configurator,
        auto.context,
        auto.logger,
    )
    auto.orchestrator = orch
    monkeypatch.setattr(sap, "_AUTOMATION", auto, raising=False)
    monkeypatch.setattr(sap, "_ORCHESTRATOR", orch, raising=False)
    monkeypatch.setattr(sap, "orchestrator", orch, raising=False)
    monkeypatch.setattr(sap, "context", auto.context, raising=False)
    monkeypatch.setattr(sap, "LOG_FILE", "log.html", raising=False)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )


# ───────────────────────────── helpers unitaires ─────────────────────────────
def _common_setup(monkeypatch, sample_config):
    """Ré-utilise `setup_init` et neutralise l’écriture de log dans une liste."""
    setup_init(monkeypatch, sample_config)
    captured: list[str] = []
    monkeypatch.setattr(
        "sele_saisie_auto.logging_service.write_log",
        lambda msg, *_a, **_k: captured.append(msg),
    )
    return captured


def test_get_next_saturday(monkeypatch, sample_config):
    _common_setup(monkeypatch, sample_config)
    assert sap.get_next_saturday_if_not_saturday("01/07/2024") == "06/07/2024"
    assert sap.get_next_saturday_if_not_saturday("06/07/2024") == "06/07/2024"


def test_est_en_mission(monkeypatch, sample_config):
    _common_setup(monkeypatch, sample_config)
    assert sap.est_en_mission("En mission") is True


def test_ajouter_jour(monkeypatch, sample_config):
    _common_setup(monkeypatch, sample_config)
    assert sap.ajouter_jour_a_jours_remplis("lundi", []) == ["lundi"]


def test_console_helpers(monkeypatch, sample_config):
    logs = _common_setup(monkeypatch, sample_config)
    # Stub subprocess & console separator to avoid real side-effects
    monkeypatch.setattr(
        utils_misc.subprocess, "run", lambda *a, **k: logs.append("cmd")
    )
    utils_misc.clear_screen()
    sap.seprateur_menu_affichage_log("log.html")
    with monkeypatch.context() as m:
        m.setattr(sap, "show_log_separator", lambda *a, **k: logs.append("sep"))
        sap.seprateur_menu_affichage_console()
    # simple présence de traces
    assert "cmd" in logs and "sep" in logs


def test_afficher_message_insertion(monkeypatch, sample_config):
    _common_setup(monkeypatch, sample_config)
    # pas d'assertion complexe : on vérifie que l’appel ne lève pas
    afficher_message_insertion(
        "lundi", "8", 0, messages.TENTATIVE_INSERTION, "log.html"
    )


def test_initialize_sets_globals(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    assert sap.context.config.url == "http://test"
    assert sap.context.config.work_schedule["lundi"] == ("En mission", "8")
    assert sap.context.project_mission_info["billing_action"] == "B"
    assert isinstance(sap._AUTOMATION.memory_config, MemoryConfig)


def test_custom_memory_config_injection(monkeypatch, sample_config):
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    mem_cfg = MemoryConfig(suffix="test")
    auto = sap.PSATimeAutomation("log.html", app_cfg, memory_config=mem_cfg)
    assert auto.encryption_service.memory_config is mem_cfg


def test_init_services(monkeypatch, sample_config):
    from sele_saisie_auto.configuration import Services

    dummy = Services(None, DummyBrowserSession("log.html"), None, None)
    called = {}

    class DummyConfigurator:
        def __init__(self, cfg):
            self.cfg = cfg

        def build_services(self, lf):
            called["args"] = (self.cfg, lf)
            return dummy

    monkeypatch.setattr(
        sap, "service_configurator_factory", lambda cfg, **kw: DummyConfigurator(cfg)
    )

    setup_init(monkeypatch, sample_config, patch_services=False)

    assert sap._AUTOMATION.services is dummy
    assert called["args"][1] == "log.html"


def test_initialize_shared_memory(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap, "shared_memory", types.SimpleNamespace(SharedMemory=DummySHM)
    )
    sap.context.encryption_service = FakeEncryptionService()
    sap.context.shared_memory_service = DummySHMService()
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    result = sap._ORCHESTRATOR.initialize_shared_memory()
    assert result.login == b"user"
    assert result.password == b"pass"


def test_main_flow(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    sap.context.config.url = "http://test"
    sap.context.config.date_cible = "06/07/2024"

    monkeypatch.setattr(sap._AUTOMATION, "log_initialisation", lambda: None)
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

    def fake_wait(driver, by, ident, *a, **k):
        class Elem:
            def __init__(self):
                self.val = "01/07/2024"

            def get_attribute(self, name):
                return self.val

            def clear(self):
                pass

            def send_keys(self, v):
                self.val = v

        if ident == Locators.DATE_INPUT.value:
            return Elem()
        return object()

    monkeypatch.setattr(sap._AUTOMATION.waiter, "wait_for_element", fake_wait)
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
    monkeypatch.setattr(sap, "sys", types.SimpleNamespace(exit=lambda: None))
    close_called = {}
    monkeypatch.setattr(
        sap.BrowserSession,
        "close",
        lambda self: close_called.setdefault("done", True),
    )
    monkeypatch.setattr(
        DummyBrowserSession,
        "close",
        lambda self: close_called.setdefault("done", True),
    )
    monkeypatch.setattr(
        sap._ORCHESTRATOR,
        "cleanup_resources",
        lambda *a, **k: close_called.setdefault("done", True),
    )
    monkeypatch.setattr(sap, "seprateur_menu_affichage_console", lambda: None)
    monkeypatch.setattr(console_ui, "ask_continue", lambda *a, **k: None)
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)

    sap.main("log.html")
    sap._ORCHESTRATOR.cleanup_resources(None, None, None)

    assert close_called["done"] is True


@pytest.fixture
def patched_orchestrator(monkeypatch):
    calls = {}

    class DummyOrchestrator:
        def __init__(self, *args, **kwargs):
            calls["init"] = (args, kwargs)
            self.run_calls: list[tuple[bool, bool]] = []

        @classmethod
        def from_components(cls, *args, **kwargs):
            calls["from_components"] = (args, kwargs)
            return cls(*args, **kwargs)

        def run(self, headless: bool = False, no_sandbox: bool = False) -> None:
            calls["run"] = (headless, no_sandbox)
            self.run_calls.append((headless, no_sandbox))

    monkeypatch.setattr(sap, "AutomationOrchestrator", DummyOrchestrator)
    return DummyOrchestrator, calls


def _build_automation(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config, patch_services=False)
    app_cfg = sap.context.config
    auto = sap.PSATimeAutomation("log.html", app_cfg)
    monkeypatch.setattr(auto, "cleanup_resources", lambda *a, **k: None)
    return auto, app_cfg


def test_orchestrator_installed(monkeypatch, sample_config, patched_orchestrator):
    auto, _ = _build_automation(monkeypatch, sample_config)
    Dummy, _ = patched_orchestrator
    auto.run()
    assert isinstance(auto.orchestrator, Dummy)


@pytest.mark.parametrize("headless,no_sandbox", [(True, True), (False, False)])
def test_run_propagates_flags(
    monkeypatch, sample_config, patched_orchestrator, headless, no_sandbox
):
    auto, _ = _build_automation(monkeypatch, sample_config)
    _, calls = patched_orchestrator
    auto.run(headless=headless, no_sandbox=no_sandbox)
    assert calls["run"] == (headless, no_sandbox)


def test_from_components_params(monkeypatch, sample_config, patched_orchestrator):
    auto, app_cfg = _build_automation(monkeypatch, sample_config)
    _, calls = patched_orchestrator
    auto.run()

    rm, nav, svc_cfg, ctx, log = calls["from_components"][0][:5]
    assert (rm, nav, ctx, log) == (
        auto.resource_manager,
        auto.page_navigator,
        auto.context,
        auto.logger,
    )
    assert isinstance(svc_cfg, ServiceConfigurator) and svc_cfg.app_config is app_cfg
