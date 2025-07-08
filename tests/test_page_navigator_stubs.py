import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402


class StubBrowserSession:
    def __init__(self):
        self.calls = []

    def go_to_default_content(self):
        self.calls.append("default")


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
    info_page = StubAdditionalInfoPage()
    helper = StubTimeSheetHelper()
    navigator = PageNavigator(session, object(), object(), info_page, helper)
    return session, info_page, helper, navigator


def test_fill_timesheet_uses_pages():
    session, info_page, helper, nav = make_navigator()
    nav.fill_timesheet("drv")
    assert helper.calls == [("run", "drv")]
    assert ("nav_add", "drv") in info_page.calls
    assert ("submit_add", "drv") in info_page.calls
    assert session.calls == ["default"]


def test_submit_timesheet_calls_save():
    _, info_page, _, nav = make_navigator()
    nav.submit_timesheet("drv")
    assert ("save", "drv") in info_page.calls
