import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

import pytest  # noqa: E402

from sele_saisie_auto import plugins  # noqa: E402
from sele_saisie_auto.app_config import (  # noqa: E402
    AppConfig,
    AppConfigRaw,
    get_default_timeout,
)
from sele_saisie_auto.encryption_utils import Credentials  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.navigation import page_navigator as pn_mod  # noqa: E402
from sele_saisie_auto.navigation.page_navigator import PageNavigator  # noqa: E402
from sele_saisie_auto.selenium_utils.waiter_factory import create_waiter  # noqa: E402
from tests.conftest import (  # noqa: E402
    DummyAdditionalInfoPage,
    DummyBrowserSession,
    DummyDateEntryPage,
    DummyLoginHandler,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_navigator():
    session = MagicMock(spec=["go_to_default_content"])
    login = MagicMock(spec=["connect_to_psatime"])
    date_page = MagicMock(
        spec=["navigate_from_home_to_date_entry_page", "process_date"]
    )
    info_page = MagicMock(
        spec=[
            "navigate_from_work_schedule_to_additional_information_page",
            "submit_and_validate_additional_information",
            "save_draft_and_validate",
        ]
    )
    helper = MagicMock(spec=["run"])
    navigator = PageNavigator(session, login, date_page, info_page, helper)
    return session, login, date_page, info_page, helper, navigator


# ---------------------------------------------------------------------------
# Unit tests using mocks
# ---------------------------------------------------------------------------


def test_login_delegates():
    _, login, _, _, _, nav = make_navigator()
    nav.login("drv", b"k", b"u", b"p")
    login.connect_to_psatime.assert_called_once_with("drv", b"k", b"u", b"p")


def test_navigate_to_date_entry():
    _, _, date_page, _, _, nav = make_navigator()
    date_page.navigate_from_home_to_date_entry_page.return_value = True
    nav.navigate_to_date_entry("drv", "2024")
    date_page.navigate_from_home_to_date_entry_page.assert_called_once_with("drv")
    date_page.process_date.assert_called_once_with("drv", "2024")


def test_fill_timesheet_calls_pages():
    session, _, _, info_page, helper, nav = make_navigator()
    nav.fill_timesheet("drv")
    helper.run.assert_called_once_with("drv")
    info_page.navigate_from_work_schedule_to_additional_information_page.assert_not_called()
    info_page.submit_and_validate_additional_information.assert_not_called()
    session.go_to_default_content.assert_not_called()


def test_submit_timesheet():
    _, _, _, info_page, _, nav = make_navigator()
    nav.submit_timesheet("drv")
    info_page.save_draft_and_validate.assert_called_once_with("drv")


def test_finalize_timesheet(monkeypatch):
    _, _, _, _, _, nav = make_navigator()
    driver = MagicMock(find_elements=True)
    detect = MagicMock()
    monkeypatch.setattr(pn_mod, "detecter_doublons_jours", detect)
    call_hook = MagicMock()
    monkeypatch.setattr(plugins, "call", call_hook)
    nav.submit_timesheet = MagicMock()

    nav.finalize_timesheet(driver)

    detect.assert_called_once_with(driver)
    call_hook.assert_called_once_with("before_submit", driver)
    nav.submit_timesheet.assert_called_once_with(driver)


def test_submit_full_timesheet():
    _, _, _, _, _, nav = make_navigator()
    nav.fill_timesheet = MagicMock()
    nav.finalize_timesheet = MagicMock()

    nav.submit_full_timesheet("drv")

    nav.fill_timesheet.assert_called_once_with("drv")
    nav.finalize_timesheet.assert_called_once_with("drv")


def test_run_sequence(monkeypatch):
    _, _, _, _, _, nav = make_navigator()
    creds = Credentials(b"k", None, b"u", None, b"p", None)
    nav.credentials = creds
    nav.date_cible = "2024"
    order = []

    monkeypatch.setattr(nav, "login", lambda *a, **k: order.append("login"))
    monkeypatch.setattr(
        nav, "navigate_to_date_entry", lambda *a, **k: order.append("navigate")
    )
    monkeypatch.setattr(nav, "fill_timesheet", lambda *a, **k: order.append("fill"))
    monkeypatch.setattr(
        nav, "finalize_timesheet", lambda *a, **k: order.append("finalize")
    )

    nav.run("drv")

    assert order == ["login", "navigate", "fill", "finalize"]


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


def test_from_automation_builds_navigator(sample_config):
    app_cfg = AppConfig.from_raw(AppConfigRaw(sample_config))
    automation = types.SimpleNamespace(
        log_file="log.html",
        logger=Logger("log.html"),
        waiter=create_waiter(get_default_timeout(app_cfg)),
        browser_session=DummyBrowserSession(),
        login_handler=DummyLoginHandler(),
        date_entry_page=DummyDateEntryPage(),
        additional_info_page=DummyAdditionalInfoPage(),
        context=types.SimpleNamespace(config=app_cfg),
    )

    nav = PageNavigator.from_automation(automation)

    assert nav.browser_session is automation.browser_session
    assert nav.login_handler is automation.login_handler
    assert nav.date_entry_page is automation.date_entry_page
    assert nav.additional_info_page is automation.additional_info_page
    assert nav.timesheet_helper is not None
