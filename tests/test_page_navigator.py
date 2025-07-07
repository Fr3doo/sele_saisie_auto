import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

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
