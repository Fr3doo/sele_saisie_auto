import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402


class StubBrowserSession:
    def __init__(self):
        self.calls = []

    def go_to_default_content(self):
        self.calls.append("default")


class StubLoginHandler:
    def __init__(self):
        self.calls = []

    def connect_to_psatime(self, driver, key, login, pwd):
        self.calls.append((driver, key, login, pwd))


class StubDateEntryPage:
    def __init__(self):
        self.calls = []

    def navigate_from_home_to_date_entry_page(self, driver):
        self.calls.append(("nav", driver))
        return True

    def process_date(self, driver, date):
        self.calls.append(("date", date))


class StubAdditionalInfoPage:
    def __init__(self):
        self.calls = []

    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        self.calls.append(("nav_add", driver))

    def submit_and_validate_additional_information(self, driver):
        self.calls.append(("submit_add", driver))

    def save_draft_and_validate(self, driver):
        self.calls.append(("save", driver))


class StubTimeSheetHelper:
    def __init__(self):
        self.calls = []

    def run(self, driver):
        self.calls.append(("run", driver))


def make_navigator():
    session = StubBrowserSession()
    login = StubLoginHandler()
    date_page = StubDateEntryPage()
    info_page = StubAdditionalInfoPage()
    helper = StubTimeSheetHelper()
    navigator = PageNavigator(session, login, date_page, info_page, helper)
    return session, login, date_page, info_page, helper, navigator


def test_run_uses_all_pages():
    session, login, date_page, info_page, helper, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.prepare(creds, "2024")
    nav.run("drv")
    assert helper.calls == [("run", "drv")]
    assert ("nav_add", "drv") in info_page.calls
    assert ("submit_add", "drv") in info_page.calls
    assert ("save", "drv") in info_page.calls
    assert ("nav", "drv") in date_page.calls
    assert ("date", "2024") in date_page.calls
    assert ("drv", b"k", b"u", b"p") in login.calls
    assert session.calls == ["default"]
