import types

import pytest

from sele_saisie_auto import saisie_automatiser_psatime as sap
from sele_saisie_auto.logger_utils import afficher_message_insertion
from sele_saisie_auto.utils import misc as utils_misc
from tests.test_saisie_automatiser_psatime import (
    DummyManager,
    DummySHM,
    DummySHMService,
    FakeEncryptionService,
    setup_init,
)

pytestmark = pytest.mark.slow


def test_initialize_date_none(monkeypatch, sample_config):
    cfg = sample_config
    cfg["settings"]["date_cible"] = "none"
    from sele_saisie_auto.app_config import AppConfig, AppConfigRaw

    app_cfg = AppConfig.from_raw(AppConfigRaw(cfg))
    monkeypatch.setattr(sap, "set_log_file_selenium", lambda lf: None)
    monkeypatch.setattr(
        sap, "EncryptionService", lambda lf, shm=None: FakeEncryptionService()
    )
    sap.initialize(
        "log.html",
        app_cfg,
        choix_user=True,
        memory_config=sap.MemoryConfig(),
    )
    monkeypatch.setattr(
        sap,
        "ConfigManager",
        lambda log_file=None: types.SimpleNamespace(load=lambda: app_cfg),
    )
    assert sap.context.config.date_cible is None


def test_clear_screen_windows(monkeypatch):
    called = []
    monkeypatch.setattr(
        utils_misc,
        "os",
        types.SimpleNamespace(name="nt"),
        raising=False,
    )
    monkeypatch.setattr(
        utils_misc.subprocess,
        "run",
        lambda cmd, *a, **k: called.append(cmd),
    )
    utils_misc.clear_screen()
    assert "cls" in called[0]


def test_ajouter_jour_a_jours_remplis_existing():
    filled_days = ["lundi"]
    assert sap.ajouter_jour_a_jours_remplis("lundi", filled_days) == ["lundi"]


def test_afficher_message_insertion_other(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "sele_saisie_auto.logger_utils.write_log",
        lambda msg, f, level: logs.append(msg),
    )
    afficher_message_insertion("mardi", "8", 1, "ok", "log.html")
    assert logs


def test_log_initialisation_no_log():
    sap._AUTOMATION = None
    with pytest.raises(sap.AutomationNotInitializedError):
        sap.log_initialisation()


def test_initialize_shared_memory_error(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap, "shared_memory", types.SimpleNamespace(SharedMemory=DummySHM)
    )
    sap.context.encryption_service = FakeEncryptionService()
    sap.context.shared_memory_service = DummySHMService()
    sap._ORCHESTRATOR.resource_manager._resource_context.encryption_service = (
        sap._ORCHESTRATOR.resource_manager._encryption_service
    )
    monkeypatch.setattr(
        sap._ORCHESTRATOR.resource_manager._encryption_service,
        "retrieve_credentials",
        lambda: sap.Credentials(
            aes_key=b"k" * 32,
            mem_key=None,
            login=b"u",
            mem_login=None,
            password=b"p",
            mem_password=None,
        ),
    )
    monkeypatch.setattr(sap, "write_log", lambda *a, **k: None)
    with pytest.raises(sap.AutomationExitError):
        sap.initialize_shared_memory()


def test_switch_to_iframe_main_target_win0_false(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._AUTOMATION.waiter, "wait_for_element", lambda *a, **k: True
    )
    monkeypatch.setattr(sap.BrowserSession, "go_to_iframe", lambda *a, **k: False)
    sap._AUTOMATION.browser_session.go_to_iframe = lambda *a, **k: False
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap._ORCHESTRATOR.switch_to_iframe_main_target_win0("drv") is False


def test_submit_date_cible_no_element(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._ORCHESTRATOR.date_entry_page, "submit_date_cible", lambda driver: False
    )
    assert sap._ORCHESTRATOR.submit_date_cible("drv") is False


def test_navigate_from_work_schedule_without_element(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    called = {}
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "navigate_from_work_schedule_to_additional_information_page",
        lambda driver: called.setdefault("nav", True),
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap._ORCHESTRATOR.navigate_from_work_schedule_to_additional_information_page("drv")
    assert called["nav"] is True


def test_submit_and_validate_additional_information_no_iframe(
    monkeypatch, sample_config
):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "submit_and_validate_additional_information",
        lambda driver: None,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    sap._ORCHESTRATOR.submit_and_validate_additional_information("drv")


def test_save_draft_and_validate_no_element(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    monkeypatch.setattr(
        sap._AUTOMATION.additional_info_page,
        "save_draft_and_validate",
        lambda driver: False,
    )
    monkeypatch.setattr(
        sap.PSATimeAutomation, "wait_for_dom", lambda self, *a, **k: None
    )
    assert sap._ORCHESTRATOR.save_draft_and_validate("drv") is False


def test_cleanup_resources_calls(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    enc = FakeEncryptionService()
    manager = DummyManager("log.html")
    sap.context.encryption_service = enc
    shm_service = DummySHMService()
    sap.context.shared_memory_service = shm_service
    sap._ORCHESTRATOR.context.shared_memory_service = shm_service
    sap._ORCHESTRATOR.resource_manager._encryption_service.shared_memory_service = (
        shm_service
    )
    sap._ORCHESTRATOR.resource_manager._credentials = sap.Credentials(
        b"k",
        "c",
        b"u",
        "n",
        b"p",
        None,
    )
    sap._ORCHESTRATOR._cleanup_callback = (
        lambda mk, ml, mp: sap._AUTOMATION.cleanup_resources(manager, mk, ml, mp)
    )
    sap._ORCHESTRATOR.browser_session = manager
    sap._ORCHESTRATOR.cleanup_resources("c", "n", None)
    assert shm_service.removed == ["c", "n"]
    assert manager.driver is None


def test_fill_and_save_timesheet(monkeypatch, sample_config):
    setup_init(monkeypatch, sample_config)
    auto = sap._AUTOMATION
    calls = []
    monkeypatch.setattr(auto, "wait_for_dom", lambda d: calls.append("wait"))
    monkeypatch.setattr(auto, "switch_to_iframe_main_target_win0", lambda d: True)
    monkeypatch.setattr(
        sap, "program_break_time", lambda *a, **k: calls.append("break")
    )
    monkeypatch.setattr(auto, "_click_action_button", lambda d: calls.append("click"))

    class DummyHelper:
        def __init__(self, *a, **k):
            pass

        def run(self, driver):
            calls.append("fill")

    monkeypatch.setattr(
        sap.remplir_jours_feuille_de_temps,
        "TimeSheetHelper",
        DummyHelper,
    )
    monkeypatch.setattr(
        auto.additional_info_page,
        "save_draft_and_validate",
        lambda d: (
            calls.append("save"),
            auto.additional_info_page._handle_save_alerts(d),
        ),
    )
    monkeypatch.setattr(
        auto.page_navigator,
        "submit_timesheet",
        lambda d: auto.additional_info_page.save_draft_and_validate(d),
    )
    auto.additional_info_page.alert_handler.handle_alerts = (
        lambda d, alert_type="save_alerts": calls.append((d, alert_type))
    )
    monkeypatch.setattr(sap, "detecter_doublons_jours", lambda d: calls.append("dup"))
    monkeypatch.setattr(sap.plugins, "call", lambda name, d: calls.append(name))

    auto._fill_and_save_timesheet("drv")

    assert ("drv", "save_alerts") in calls
