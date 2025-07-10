import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402


class DummyLoginHandler:
    def __init__(self):
        self.calls = []

    def connect_to_psatime(self, driver, key, login, pwd):
        self.calls.append((driver, key, login, pwd))


class DummyDatePage:
    def __init__(self):
        self.calls = []

    def navigate_from_home_to_date_entry_page(self, driver):
        self.calls.append("nav")
        return True

    def process_date(self, driver, date):
        self.calls.append(("date", date))


class DummyInfoPage:
    def __init__(self):
        self.calls = []

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        self.calls.append("submit_add")

    def save_draft_and_validate(self, driver):
        self.calls.append("save")


class DummyHelper:
    def __init__(self):
        self.calls = []

    def run(self, driver):
        self.calls.append(driver)


class DummySession:
    def __init__(self):
        self.calls = []

    def go_to_default_content(self):
        self.calls.append("default")


def make_navigator():
    session = DummySession()
    login = DummyLoginHandler()
    date_page = DummyDatePage()
    info_page = DummyInfoPage()
    helper = DummyHelper()
    return (
        session,
        login,
        date_page,
        info_page,
        helper,
        PageNavigator(session, login, date_page, info_page, helper),
    )


def test_login_delegates():
    session, login, _, _, _, nav = make_navigator()
    nav.login("drv", b"k", b"u", b"p")
    assert login.calls == [("drv", b"k", b"u", b"p")]


def test_navigate_to_date_entry():
    _, _, date_page, _, _, nav = make_navigator()
    nav.navigate_to_date_entry("drv", "2024")
    assert "nav" in date_page.calls
    assert ("date", "2024") in date_page.calls


def test_fill_timesheet_calls_pages():
    session, _, _, info_page, helper, nav = make_navigator()
    nav.fill_timesheet("drv")
    assert helper.calls == ["drv"]
    assert "nav_add" in info_page.calls
    assert "submit_add" in info_page.calls
    assert "default" in session.calls


def test_submit_timesheet():
    _, _, _, info_page, _, nav = make_navigator()
    nav.submit_timesheet("drv")
    assert "save" in info_page.calls


class LoggedDummyLoginHandler(DummyLoginHandler):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def connect_to_psatime(self, driver, key, login, pwd):
        super().connect_to_psatime(driver, key, login, pwd)
        self.log.append("login")


class LoggedDummyDatePage(DummyDatePage):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def navigate_from_home_to_date_entry_page(self, driver):
        result = super().navigate_from_home_to_date_entry_page(driver)
        self.log.append("navigate")
        return result

    def process_date(self, driver, date):
        super().process_date(driver, date)
        self.log.append("process")


class LoggedDummyInfoPage(DummyInfoPage):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        super().navigate_from_work_schedule_to_additional_information_page(driver)
        self.log.append("nav_add")

    def submit_and_validate_additional_information(self, driver):
        super().submit_and_validate_additional_information(driver)
        self.log.append("submit_add")

    def save_draft_and_validate(self, driver):
        super().save_draft_and_validate(driver)
        self.log.append("save")


class LoggedDummyHelper(DummyHelper):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def run(self, driver):
        super().run(driver)
        self.log.append("fill")


class LoggedDummySession(DummySession):
    def __init__(self, log):
        super().__init__()
        self.log = log

    def go_to_default_content(self):
        super().go_to_default_content()
        self.log.append("default")


def make_logged_navigator():
    log = []
    session = LoggedDummySession(log)
    login = LoggedDummyLoginHandler(log)
    date_page = LoggedDummyDatePage(log)
    info_page = LoggedDummyInfoPage(log)
    helper = LoggedDummyHelper(log)
    navigator = PageNavigator(session, login, date_page, info_page, helper)
    return log, navigator


def test_full_sequence_order():
    log, nav = make_logged_navigator()
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


def test_prepare_sets_attributes():
    _, _, _, _, _, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.prepare(creds, "2024")
    assert nav.credentials is creds
    assert nav.date_cible == "2024"


def test_run_requires_prepare():
    _, _, _, _, _, nav = make_navigator()
    with pytest.raises(RuntimeError):
        nav.run("drv")


def test_run_calls_sequence():
    log, nav = make_logged_navigator()
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
