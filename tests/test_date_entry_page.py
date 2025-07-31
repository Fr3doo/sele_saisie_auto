import sys
import types
from pathlib import Path

import pytest

from sele_saisie_auto.exceptions import AutomationExitError

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.automation.date_entry_page import DateEntryPage  # noqa: E402


class DummyAutomation:
    def __init__(self):
        self.log_file = "log.html"
        self.browser_session = types.SimpleNamespace(
            go_to_default_content=lambda *a, **k: None,
            go_to_iframe=lambda *a, **k: True,
            click=lambda *a, **k: None,
            fill_input=lambda *a, **k: None,
        )

    def wait_for_dom(self, driver, max_attempts: int = 3):
        pass

    def switch_to_iframe_main_target_win0(self, driver):
        return True


class DummyNavigator:
    def __init__(self, session):
        self.browser_session = session


def test_navigate_from_home_to_date_entry_page(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    seq = iter([True, True])
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: next(seq))
    clicks = []
    monkeypatch.setattr(
        dummy.browser_session, "click", lambda *a, **k: clicks.append(True)
    )
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    assert page.navigate_from_home_to_date_entry_page("drv") is True
    assert len(clicks) == 2


def test_handle_date_input(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))

    class Input:
        def __init__(self):
            self.val = "01/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: inp)
    result = {}
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.modifier_date_input",
        lambda elem, val, msg: result.setdefault("v", val),
    )
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    page.handle_date_input("drv", "10/07/2024")
    assert result["v"] == "10/07/2024"


def test_handle_date_input_auto(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))

    class Input:
        def __init__(self):
            self.val = "01/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: inp)
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.get_next_saturday_if_not_saturday",
        lambda d: "06/07/2024",
    )
    result = {}
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.modifier_date_input",
        lambda elem, val, msg: result.setdefault("v", val),
    )
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    page.handle_date_input("drv", None)
    assert result["v"] == "06/07/2024"


def test_handle_date_input_no_change(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))

    class Input:
        def __init__(self):
            self.val = "06/07/2024"

        def get_attribute(self, _):
            return self.val

    inp = Input()
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: inp)
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.get_next_saturday_if_not_saturday",
        lambda d: "06/07/2024",
    )
    monkeypatch.setattr(
        "sele_saisie_auto.saisie_automatiser_psatime.modifier_date_input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError()),
    )
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.logging_service.write_log",
        lambda msg, f, level: logs.append(msg),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.date_entry_page.write_log",
        lambda msg, f, level: logs.append(msg),
    )
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    page.handle_date_input("drv", None)
    assert "Aucune modification" in logs[0]


def test_submit_date_cible(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: True)
    actions = []
    monkeypatch.setattr(
        dummy.browser_session,
        "fill_input",
        lambda *a, **k: actions.append(True),
    )
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    assert page.submit_date_cible("drv") is True
    assert actions


def test_submit_date_cible_no_element(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: False)
    monkeypatch.setattr(DateEntryPage, "wait_for_dom", lambda self, d: None)
    assert page.submit_date_cible("drv") is False


def test_click_action_button(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: True)
    clicks = []
    monkeypatch.setattr(
        dummy.browser_session, "click", lambda *a, **k: clicks.append(True)
    )
    page._click_action_button("drv", True)
    assert clicks


def test_click_action_button_copy(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    monkeypatch.setattr(page.waiter, "wait_for_element", lambda *a, **k: True)
    clicks = []
    monkeypatch.setattr(
        dummy.browser_session, "click", lambda *a, **k: clicks.append(True)
    )
    page._click_action_button("drv", False)
    assert clicks


def test_handle_date_alert(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))
    calls = []

    def fake_handle(driver):
        calls.append("handled")
        raise AutomationExitError("stop")

    monkeypatch.setattr(page.alert_handler, "handle_date_alert", fake_handle)
    with pytest.raises(AutomationExitError):
        page._handle_date_alert("drv")
    assert "handled" in calls


def test_process_date(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))

    calls = []
    monkeypatch.setattr(
        page,
        "handle_date_input",
        lambda driver, date: calls.append(("input", date)),
    )
    monkeypatch.setattr(
        page,
        "submit_date_cible",
        lambda driver: calls.append("submit") or True,
    )
    monkeypatch.setattr(
        page.alert_handler,
        "handle_date_alert",
        lambda driver: calls.append("alert"),
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.date_entry_page.program_break_time",
        lambda *a, **k: calls.append("wait"),
    )

    page.process_date("drv", "01/01/2024")

    assert calls == [("input", "01/01/2024"), "wait", "submit", "alert"]


def test_process_date_no_submit(monkeypatch):
    dummy = DummyAutomation()
    page = DateEntryPage(dummy, page_navigator=DummyNavigator(dummy.browser_session))

    calls = []
    monkeypatch.setattr(page, "handle_date_input", lambda *a: calls.append("input"))
    monkeypatch.setattr(
        page, "submit_date_cible", lambda d: calls.append("submit") or False
    )
    monkeypatch.setattr(
        page.alert_handler, "handle_date_alert", lambda d: calls.append("alert")
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.date_entry_page.program_break_time",
        lambda *a, **k: calls.append("wait"),
    )

    page.process_date("drv", None)

    assert calls == ["input", "wait", "submit"]
