import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402
from tests.conftest import (  # noqa: E402
    DummyDatePage,
    DummyHelper,
    DummyInfoPage,
    DummyLoginHandler,
    DummySession,
)
from tests.conftest import LoggedDummyDateEntryPage as LoggedDummyDatePage  # noqa: E402
from tests.conftest import (  # noqa: E402
    LoggedDummyHelper,
    LoggedDummyInfoPage,
    LoggedDummyLoginHandler,
    LoggedDummySession,
)


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
