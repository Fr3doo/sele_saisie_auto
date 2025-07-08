import types

import pytest

from sele_saisie_auto import console_ui, plugins
from sele_saisie_auto import saisie_automatiser_psatime as sap
from tests.test_saisie_automatiser_psatime import setup_init

pytestmark = pytest.mark.slow


def test_register_and_call():
    plugins.clear()
    calls = []
    plugins.register("before_submit", lambda d: calls.append(d))
    plugins.call("before_submit", "drv")
    assert calls == ["drv"]


def test_run_invokes_hook(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    sap.context.config.url = "http://test"
    sap.context.config.date_cible = "06/07/2024"
    sap._AUTOMATION.choix_user = True

    monkeypatch.setattr(sap, "log_initialisation", lambda: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "initialize_shared_memory",
        lambda self: sap.Credentials(
            aes_key=b"k",
            mem_key=object(),
            login=b"user",
            mem_login=object(),
            password=b"pass",
            mem_password=object(),
        ),
    )

    monkeypatch.setattr(sap.LoginHandler, "connect_to_psatime", lambda *a, **k: None)
    monkeypatch.setattr(sap.DateEntryPage, "handle_date_input", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "submit_date_cible", lambda *a, **k: False
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "navigate_from_home_to_date_entry_page",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "navigate_from_work_schedule_to_additional_information_page",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "submit_and_validate_additional_information",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "switch_to_iframe_main_target_win0", lambda *a, **k: True
    )
    monkeypatch.setattr(
        "sele_saisie_auto.automation.browser_session.BrowserSession.go_to_default_content",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: object()
    )
    monkeypatch.setattr(sap, "modifier_date_input", lambda *a, **k: None)
    monkeypatch.setattr(sap.BrowserSession, "go_to_iframe", lambda *a, **k: True)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    monkeypatch.setattr(
        sap._AUTOMATION.browser_session.waiter,
        "wait_until_dom_is_stable",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        sap._AUTOMATION.browser_session.waiter,
        "wait_for_dom_ready",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(sap, "program_break_time", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.remplir_jours_feuille_de_temps.TimeSheetHelper,
        "run",
        lambda self, drv: None,
    )
    monkeypatch.setattr(sap, "traiter_description", lambda *a, **k: None)
    monkeypatch.setattr(sap, "detecter_doublons_jours", lambda *a, **k: None)
    monkeypatch.setattr(sap, "sys", types.SimpleNamespace(exit=lambda: None))
    monkeypatch.setattr(sap, "seprateur_menu_affichage_console", lambda: None)
    monkeypatch.setattr(console_ui, "ask_continue", lambda *a, **k: None)
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)

    calls = []
    plugins.clear()
    plugins.register("before_submit", lambda d: calls.append("hook"))
    monkeypatch.setattr(
        sap.plugins,
        "call",
        lambda name, *a, **k: calls.append("hook") if name == "before_submit" else None,
    )

    def fake_save(self, driver):
        calls.append("save")
        return False

    monkeypatch.setattr(sap.PSATimeAutomation, "save_draft_and_validate", fake_save)
    monkeypatch.setattr(
        sap.BrowserSession,
        "close",
        lambda self: calls.append("close"),
    )

    sap.main("log.html")

    assert "close" in calls


def test_hook_decorator_registers():
    plugins.clear()
    calls = []

    @plugins.hook("after_run")
    def cb(data):
        calls.append(data)

    plugins.call("after_run", 123)
    assert calls == [123]


def test_call_returns_list_of_results():
    plugins.clear()

    @plugins.hook("after_run")
    def plus_one(x):
        return x + 1

    @plugins.hook("after_run")
    def times_two(x):
        return x * 2

    results = plugins.call("after_run", 3)
    assert results == [4, 6]
