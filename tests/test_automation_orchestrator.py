import types
from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto.app_config import AppConfig, AppConfigRaw
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.orchestration import AutomationOrchestrator


class DummyBrowserSession:
    def __init__(self):
        self.open_calls = []
        self.driver = "drv"
        self.waiter = None

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


def test_run_calls_services(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    logger = Logger("log.html")
    session = DummyBrowserSession()
    login = DummyLoginHandler()
    date_page = DummyDateEntryPage()
    add_page = DummyAddPage()

    orch = AutomationOrchestrator(
        app_cfg,
        logger,
        session,
        login,
        date_page,
        add_page,
        timesheet_helper_cls=DummyHelper,
    )

    orch.run(b"k" * 32, b"user", b"pwd")

    assert session.open_calls[0][0] == app_cfg.url
    assert login.calls
    assert DummyHelper.ran == session.driver
    assert "nav" in date_page.calls
    assert "nav_add" in add_page.calls
