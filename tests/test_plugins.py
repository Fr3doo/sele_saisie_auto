import types

import console_ui
import plugins
import saisie_automatiser_psatime as sap
from tests.test_saisie_automatiser_psatime import DummyManager, setup_init


def test_register_and_call():
    plugins.clear()
    calls = []
    plugins.register("before_submit", lambda d: calls.append(d))
    plugins.call("before_submit", "drv")
    assert calls == ["drv"]


def test_run_invokes_hook(monkeypatch):
    setup_init(monkeypatch)
    sap.context.config.url = "http://test"
    sap.context.config.date_cible = "06/07/2024"
    sap.CHOIX_USER = True

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
    monkeypatch.setattr(sap, "SeleniumDriverManager", DummyManager)

    monkeypatch.setattr(
        sap.PSATimeAutomation, "connect_to_psatime", lambda *a, **k: None
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "handle_date_input", lambda *a, **k: None
    )
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
    monkeypatch.setattr(sap, "switch_to_default_content", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_element", lambda *a, **k: object())
    monkeypatch.setattr(sap, "modifier_date_input", lambda *a, **k: None)
    monkeypatch.setattr(sap, "switch_to_iframe_by_id_or_name", lambda *a, **k: True)
    monkeypatch.setattr(sap, "click_element_without_wait", lambda *a, **k: None)
    monkeypatch.setattr(sap, "send_keys_to_element", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_until_dom_is_stable", lambda *a, **k: None)
    monkeypatch.setattr(sap, "wait_for_dom_ready", lambda *a, **k: None)
    monkeypatch.setattr(sap, "program_break_time", lambda *a, **k: None)
    monkeypatch.setattr(
        sap.remplir_jours_feuille_de_temps, "main", lambda *a, **k: None
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

    def fake_save(self, driver):
        calls.append("save")
        return False

    monkeypatch.setattr(sap.PSATimeAutomation, "save_draft_and_validate", fake_save)
    monkeypatch.setattr(
        sap.PSATimeAutomation,
        "cleanup_resources",
        lambda self, *a, **k: calls.append("cleanup"),
    )

    sap.main("log.html")

    assert "hook" in calls
    assert "save" in calls
