import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402


class StubLoginHandler:
    def __init__(self, log):
        self.log = log

    def connect_to_psatime(self, driver, key, login, pwd):
        self.log.append("login")


class StubDateEntryPage:
    def __init__(self, log):
        self.log = log

    def navigate_from_home_to_date_entry_page(self, driver):
        self.log.append("navigate")
        return True

    def process_date(self, driver, date):
        self.log.append("process")


class StubAdditionalInfoPage:
    def __init__(self, log):
        self.log = log

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.log.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        self.log.append("submit_add")

    def save_draft_and_validate(self, driver):
        self.log.append("save")


class StubTimeSheetHelper:
    def __init__(self, log):
        self.log = log

    def run(self, driver):
        self.log.append("fill")


class StubBrowserSession:
    def __init__(self, log):
        self.log = log

    def go_to_default_content(self):
        self.log.append("default")


def make_navigator():
    log = []
    navigator = PageNavigator(
        StubBrowserSession(log),
        StubLoginHandler(log),
        StubDateEntryPage(log),
        StubAdditionalInfoPage(log),
        StubTimeSheetHelper(log),
    )
    return log, navigator


def test_run_without_prepare_raises():
    log, nav = make_navigator()
    with pytest.raises(RuntimeError):
        nav.run("drv")
    assert not log


def test_run_calls_dependencies_in_order():
    log, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.prepare(creds, "2024")
    nav.run("drv")
    assert log == [
        "login",
        "navigate",
        "process",
        "fill",
        "nav_add",
        "submit_add",
        "default",
        "save",
    ]
