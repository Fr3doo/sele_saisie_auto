import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw  # noqa: E402
from sele_saisie_auto.automation import (  # noqa: E402
    AdditionalInfoPage,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.navigation import PageNavigator  # noqa: E402
from sele_saisie_auto.orchestration import AutomationOrchestrator  # noqa: E402
from sele_saisie_auto.remplir_jours_feuille_de_temps import (  # noqa: E402
    context_from_app_config,
)
from sele_saisie_auto.resources import resource_manager  # noqa: E402
from sele_saisie_auto.saisie_context import SaisieContext  # noqa: E402
from tests.conftest import FakeEncryptionService  # noqa: E402


class DummyConfigManager:
    def __init__(self, log_file: str) -> None:
        self.log_file = log_file

    def load(self):
        return APP_CFG


class DummyManager:
    def __init__(self, log_file: str, app_config=None) -> None:
        self.log_file = log_file
        self.open_calls = []

    def open(self, url, fullscreen=False, headless=False, no_sandbox=False):
        self.open_calls.append((url, fullscreen, headless, no_sandbox))
        return "drv"

    def close(self):
        pass


class DummyWaiter:
    def __init__(self):
        self.calls = []

    def wait_for_element(self, *a, **k):
        self.calls.append(("wait", a, k))
        return True

    def wait_for_dom_ready(self, *a, **k):
        self.calls.append("ready")

    def wait_until_dom_is_stable(self, *a, **k):
        self.calls.append("stable")
        return True


dummy_waiter = DummyWaiter()


class DummyHelper:
    def __init__(self, ctx, logger, waiter=None):
        self.calls = []

    def run(self, driver):
        self.calls.append(driver)


class DummySHMService:
    def __init__(self):
        self.removed = []

    def supprimer_memoire_partagee_securisee(self, mem):
        self.removed.append(mem)


CREDS = types.SimpleNamespace(
    aes_key=b"k" * 32,
    mem_key=object(),
    login=b"user",
    mem_login=object(),
    password=b"pwd",
    mem_password=object(),
)


class DummyAutomation:
    def __init__(self, log_file, ctx, session, logger):
        self.log_file = log_file
        self.context = ctx
        self.browser_session = session
        self.logger = logger

    def wait_for_dom(self, driver, max_attempts: int = 3):
        pass

    def switch_to_iframe_main_target_win0(self, driver):
        return True


def test_full_automation(monkeypatch, sample_config):
    global APP_CFG
    APP_CFG = AppConfig.from_raw(AppConfigRaw(sample_config))
    log_file = "log.html"
    logger = Logger(log_file)

    monkeypatch.setattr(resource_manager, "ConfigManager", DummyConfigManager)
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.SeleniumDriverManager",
        DummyManager,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.selenium_utils.waiter_factory.create_waiter",
        lambda timeout: dummy_waiter,
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.additional_info_page.ExtraInfoHelper",
        lambda *a, **k: types.SimpleNamespace(traiter_description=lambda *a, **k: None),
    )

    with resource_manager.ResourceManager(
        log_file, FakeEncryptionService(log_file)
    ) as rm:
        ctx = SaisieContext(APP_CFG, rm._encryption_service, DummySHMService(), {}, [])
        automation = DummyAutomation(log_file, ctx, rm._session, logger)
        login = LoginHandler(log_file, rm._encryption_service, rm._session)
        date_page = DateEntryPage(automation)
        add_page = AdditionalInfoPage(automation)
        helper = DummyHelper(
            context_from_app_config(APP_CFG, log_file), logger, waiter=dummy_waiter
        )
        navigator = PageNavigator(rm._session, login, date_page, add_page, helper)
        orch = AutomationOrchestrator.from_components(
            rm,
            navigator,
            types.SimpleNamespace(app_config=APP_CFG),
            ctx,
            logger,
            timesheet_helper_cls=DummyHelper,
        )

        calls = []
        monkeypatch.setattr(
            orch.login_handler,
            "connect_to_psatime",
            lambda *a, **k: calls.append("login"),
        )
        monkeypatch.setattr(
            orch.page_navigator,
            "run",
            lambda *a, **k: calls.extend(
                ["login", "navigate", "process", "fill", "submit"]
            ),
        )
        monkeypatch.setattr(orch, "initialize_shared_memory", lambda: CREDS)
        monkeypatch.setattr(orch, "wait_for_dom", lambda *a, **k: None)
        monkeypatch.setattr(
            orch, "switch_to_iframe_main_target_win0", lambda *a, **k: None
        )
        monkeypatch.setattr(
            orch, "cleanup_resources", lambda *a, **k: calls.append("cleanup")
        )
        monkeypatch.setattr(
            "sele_saisie_auto.console_ui.ask_continue", lambda *a, **k: None
        )

        orch.run(headless=True, no_sandbox=True)

        assert calls == ["login", "navigate", "process", "fill", "submit", "cleanup"]
