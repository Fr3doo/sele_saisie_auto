import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402
from tests.conftest import (  # noqa: E402
    DummyAdditionalInfoPage as StubAdditionalInfoPage,
)
from tests.conftest import DummyDateEntryPage as StubDateEntryPage  # noqa: E402
from tests.conftest import DummyLoginHandler as StubLoginHandler  # noqa: E402
from tests.conftest import DummySession as StubBrowserSession  # noqa: E402
from tests.conftest import DummyTimeSheetHelper as StubTimeSheetHelper  # noqa: E402


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
    assert helper.calls == ["drv"]
    assert "nav_add" in info_page.calls
    assert "submit_add" in info_page.calls
    assert "save" in info_page.calls
    assert "nav" in date_page.calls
    assert ("date", "2024") in date_page.calls
    assert ("drv", b"k", b"u", b"p") in login.calls
    assert session.calls == ["default"]
