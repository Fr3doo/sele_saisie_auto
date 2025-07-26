import sys
import types
from pathlib import Path

import pytest

from sele_saisie_auto import console_ui
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.utils import misc as utils_misc

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import messages  # noqa: E402
from sele_saisie_auto import saisie_automatiser_psatime as sap  # noqa: E402
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


class DummyBrowserSession:
    def __init__(self, log_file, app_config=None, waiter=None):
        self.log_file = log_file
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


def setup_init(monkeypatch, cfg, *, patch_services: bool = True):
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(sap, "SharedMemoryService", lambda logger: DummySHMService())
    monkeypatch.setattr(sap, "LoginHandler", DummyLoginHandler)
    monkeypatch.setattr(sap, "DateEntryPage", DummyDateEntryPage)
    monkeypatch.setattr(sap, "AdditionalInfoPage", DummyAdditionalInfoPage)
    from sele_saisie_auto.resources import resource_manager as rm

    if patch_services:
        from sele_saisie_auto.configuration import Services
        from sele_saisie_auto.selenium_utils.waiter_factory import get_waiter

        def fake_build(cfg_b, lf_b):
            waiter = get_waiter(cfg_b)
            session = sap.BrowserSession(lf_b, cfg_b, waiter=waiter)
            enc = FakeEncryptionService()
            login = sap.LoginHandler(lf_b, enc, session)
            return Services(enc, session, waiter, login)

        monkeypatch.setattr(sap, "build_services", fake_build)
        waiter = get_waiter(app_cfg)
        monkeypatch.setattr(
            rm,
            "ConfigManager",
            lambda log_file: types.SimpleNamespace(load=lambda: app_cfg),
        )
        monkeypatch.setattr(
            rm,
            "BrowserSession",
            lambda log_file, cfg=app_cfg: DummyBrowserSession(
                log_file, cfg, waiter=waiter
            ),
        )
        monkeypatch.setattr(
            sap,
            "ResourceManager",
            lambda log_file: rm.ResourceManager(log_file, FakeEncryptionService()),
        )
    else:
        monkeypatch.setattr(
            sap,
            "ResourceManager",
            lambda log_file: rm.ResourceManager(log_file, FakeEncryptionService()),
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
    monkeypatch.setattr(sap, "LOG_FILE", "log.html", raising=False)
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )


def test_helpers(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    logs = []
    monkeypatch.setattr(sap, "write_log", lambda msg, f, level: logs.append(msg))
    assert sap.get_next_saturday_if_not_saturday("01/07/2024") == "06/07/2024"
    assert sap.get_next_saturday_if_not_saturday("06/07/2024") == "06/07/2024"
    assert sap.est_en_mission("En mission") is True
    filled_days = []
    assert sap.ajouter_jour_a_jours_remplis("lundi", filled_days) == ["lundi"]
    sap.afficher_message_insertion(
        "lundi", "8", 0, messages.TENTATIVE_INSERTION, "log.html"
    )
    monkeypatch.setattr(
        utils_misc.subprocess,
        "run",
        lambda cmd, *a, **k: logs.append(cmd),
    )
    utils_misc.clear_screen()
    sap.seprateur_menu_affichage_log("log.html")
    with monkeypatch.context() as m:
        called = []
        m.setattr(console_ui, "show_separator", lambda: called.append(True))
        sap.seprateur_menu_affichage_console()
    sap.log_initialisation()
    assert messages


def test_initialize_sets_globals(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    assert sap.context.config.url == "http://test"
    assert sap.context.config.work_schedule["lundi"] == ("En mission", "8")
    assert sap.context.project_mission_info["billing_action"] == "B"
    assert sap._AUTOMATION.choix_user is True
    assert isinstance(sap._AUTOMATION.memory_config, sap.MemoryConfig)


def test_init_services(monkeypatch, sample_config):
    from sele_saisie_auto.configuration import Services

    dummy = Services(None, None, None, None)
    called = {}

    def fake_build(cfg, lf):
        called["args"] = (cfg, lf)
        return dummy

    monkeypatch.setattr(sap, "build_services", fake_build)

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
    result = sap.initialize_shared_memory()
    assert result.login == b"user"
    assert result.password == b"pass"


def test_main_flow(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    sap.context.config.url = "http://test"
    sap.context.config.date_cible = "06/07/2024"
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


def test_run_delegates_to_orchestrator(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    app_cfg = sap.context.config

    called = {}

    class DummyOrchestrator:
        def __init__(self, *args, **kwargs):
            called["init"] = (args, kwargs)
            self.browser_session = DummyBrowserSession("log.html")
            self.run_called = 0
            self.run_args = None

        @classmethod
        def from_components(cls, *a, **k):
            called["from_components"] = (a, k)
            return cls(*a, **k)

        def run(self, headless=False, no_sandbox=False):
            called["run"] = (headless, no_sandbox)
            self.run_called += 1
            self.run_args = (headless, no_sandbox)

    monkeypatch.setattr(sap, "AutomationOrchestrator", DummyOrchestrator)

    auto = sap.PSATimeAutomation("log.html", app_cfg)
    monkeypatch.setattr(auto, "cleanup_resources", lambda *a, **k: None)

    auto.run(headless=True, no_sandbox=True)

    assert isinstance(auto.orchestrator, DummyOrchestrator)
    assert auto.orchestrator.run_called == 1
    assert auto.orchestrator.run_args == (True, True)
    assert called["from_components"][0][0] is auto.resource_manager
    assert called["from_components"][0][1] is auto.page_navigator
    assert isinstance(called["from_components"][0][2], ServiceConfigurator)
    assert called["from_components"][0][2].app_config is app_cfg
    assert called["from_components"][0][3] is auto.context
    assert called["from_components"][0][4] is auto.logger
    assert called["from_components"][1]["choix_user"] is True
    assert called["run"] == (True, True)
