import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.orchestration import AutomationOrchestrator  # noqa: E402
from sele_saisie_auto.saisie_automatiser_psatime import SaisieContext  # noqa: E402


class DummyBrowserSession:
    def __init__(self):
        self.open_calls = []
        self.driver = "drv"
        self.waiter = types.SimpleNamespace(wait_for_element=lambda *a, **k: True)

    def wait_for_dom(self, driver):
        self.wait_called = True

    def go_to_iframe(self, frame_id):
        self.iframe_called = frame_id
        return True

    def open(self, url, headless=False, no_sandbox=False):
        self.open_calls.append((url, headless, no_sandbox))
        return self.driver

    def go_to_default_content(self):
        self.default_called = True

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class DummyLoginHandler:
    def __init__(self):
        self.calls = []

    def connect_to_psatime(self, driver, key, login, pwd):
        self.calls.append((driver, key, login, pwd))


class DummyDateEntryPage:
    def __init__(self):
        self.calls = []

    def navigate_from_home_to_date_entry_page(self, driver):
        self.calls.append("nav")
        return True

    def process_date(self, driver, date):
        self.calls.append(("date", date))

    def _click_action_button(self, driver, create_new):
        self.calls.append("click")

    def submit_date_cible(self, driver):
        self.calls.append("submit")


class DummyAddPage:
    def __init__(self):
        self.calls = []

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        self.calls.append("submit_add")

    def save_draft_and_validate(self, driver):
        self.calls.append("save")


class DummyHelper:
    ran = None

    def __init__(self, ctx, logger, waiter=None):
        self.ctx = ctx
        self.logger = logger
        self.waiter = waiter

    def run(self, driver):
        DummyHelper.ran = driver


def test_run_calls_services(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    session = DummyBrowserSession()
    login = DummyLoginHandler()
    date_page = DummyDateEntryPage()
    add_page = DummyAddPage()
    ctx = SaisieContext(app_cfg, None, None, {}, [])

    orch = AutomationOrchestrator(
        app_cfg,
        logger,
        session,
        login,
        date_page,
        add_page,
        ctx,
        True,
        timesheet_helper_cls=DummyHelper,
    )

    # Stub out heavy selenium helpers
    orch.wait_for_dom = lambda d: None
    orch.switch_to_iframe_main_target_win0 = lambda d: True
    orch.save_draft_and_validate = lambda d: True
    orch.browser_session.go_to_default_content = lambda: None
    orch.browser_session.waiter = types.SimpleNamespace(
        wait_for_element=lambda *a, **k: True
    )
    orch.date_entry_page._click_action_button = lambda d, c: None
    orch.additional_info_page._handle_save_alerts = lambda d: None
    from sele_saisie_auto import plugins
    from sele_saisie_auto.orchestration import automation_orchestrator as orch_mod

    monkeypatch.setattr(orch_mod, "detecter_doublons_jours", lambda *a, **k: None)
    monkeypatch.setattr(plugins, "call", lambda *a, **k: None)

    orch.run(b"k" * 32, b"user", b"pwd")

    assert session.open_calls[0][0] == app_cfg.url
    assert login.calls
    assert DummyHelper.ran == session.driver
    assert "nav" in date_page.calls
    assert "nav_add" in add_page.calls


def test_wrappers(monkeypatch, sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    orch = AutomationOrchestrator(
        app_cfg,
        Logger("log.html"),
        DummyBrowserSession(),
        DummyLoginHandler(),
        DummyDateEntryPage(),
        DummyAddPage(),
        SaisieContext(app_cfg, None, None, {}, []),
        True,
        timesheet_helper_cls=DummyHelper,
    )

    monkeypatch.setattr(orch.browser_session, "wait_for_dom", lambda d: None)
    monkeypatch.setattr(orch, "switch_to_iframe_main_target_win0", lambda d: True)
    orch.navigate_from_home_to_date_entry_page("drv")
    orch.submit_date_cible("drv")
    orch.navigate_from_work_schedule_to_additional_information_page("drv")
    orch.submit_and_validate_additional_information("drv")
    orch.save_draft_and_validate("drv")
